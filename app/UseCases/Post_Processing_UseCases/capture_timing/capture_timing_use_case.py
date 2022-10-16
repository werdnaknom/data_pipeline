from __future__ import annotations

import typing as t
import itertools
from collections import defaultdict, OrderedDict

import pandas as pd

import matplotlib.pyplot as plt
import numpy as np

from app.UseCases.Post_Processing_UseCases.post_processing_use_case import \
    PostProcessingUseCase
from app.shared.Entities import WaveformEntity
from app.shared.Requests.requests import ValidRequestObject

from app import globalConfig


class CaptureTimingRequestObject(ValidRequestObject):
    groupby_list: t.List[str]
    df: pd.DataFrame

    def __init__(self, df: pd.DataFrame):
        self.groupby_list = ['runid', 'capture']
        self.df = df

    @classmethod
    def from_dict(cls, adict) -> CaptureTimingRequestObject:
        return cls(**adict)


class CaptureTimingUseCase(PostProcessingUseCase):
    sheet_name = "Timing"
    EDGE_RAIL_COLUMN_HEADER = "edge_rail"
    TRACE_ORDER_COLUMN_HEADER = "trace_order"
    POWER_ON_TIME_COLUMN_HEADER = "power_on_time_spec"
    TIME_DELTA_COLUMN_HEADER = "time_delta"
    CURRENT_RAIL_COLUMN_HEADER = "current_rail"
    CAPTURE_RAMP_T0 = "capture_t0"
    CAPTURE_T0_INDEX = "capture_t0_index"
    RAIL_POWERON_FROM_T0 = "t0_to_poweron"
    TOTAL_POWERON_TIME = "total_poweron_time"
    POWERON_INDEX = "poweron_index"

    def _test_specific_columns(self):
        return [self.EDGE_RAIL_COLUMN_HEADER, self.TRACE_ORDER_COLUMN_HEADER,
                self.POWER_ON_TIME_COLUMN_HEADER, self.TIME_DELTA_COLUMN_HEADER]

    def post_process(self, request_object: CaptureTimingRequestObject) -> \
            pd.DataFrame:
        '''
        Takes the input dataframe and groups by each runid/capture
        combination to find the power-on timing for each rail in the capture.

        @param request_object: Capture timing request object
        @return:
        '''

        final_timed_df = pd.DataFrame()
        for filter, groupby_df in request_object.df.groupby(
                by=request_object.groupby_list):
            valid_df = self._validate_runid_capture_for_timing(df=groupby_df)
            timing_df = self.update_df_with_t0_and_timing(df=valid_df)
            final_timed_df = pd.concat([final_timed_df, timing_df],
                                       ignore_index=True)

            '''
            # Validate Capture has an EDGE rail and it's at position zero
            valid_df = self._validate_runid_capture_for_timing(df=groupby_df)

            # Determine first rail
            # All the other rails will be compared against the first rail.
            first_edge_wf = self._determine_first_rail(df=valid_df)

            wfs = self.load_waveforms(df=valid_df)

            for wf in wfs:
                plt.plot(wf.x_axis_in_milliseconds(), wf.y_axis())
                print(wf.testpoint, wf.steady_state_index())

            # plt.show()
            '''
        return final_timed_df

    def _update_valid_voltage_df_column(self, df: pd.DataFrame) -> \
            pd.DataFrame:
        valid_voltage_column = "valid_voltage"
        spec_min_column = "spec_min"
        testpoint_column = "testpoint"

        for unique_tp in df[testpoint_column].unique():
            tp_df = df[df[testpoint_column] == unique_tp]

            if spec_min_column in tp_df[valid_voltage_column].unique():
                df.at[tp_df.index, valid_voltage_column] = tp_df[
                    spec_min_column].values[0]

        df[valid_voltage_column] = df[valid_voltage_column].astype(float)

        return df

    def _validate_runid_capture_for_timing(self,
                                           df: pd.DataFrame) -> pd.DataFrame:
        # Drop Current Rails
        no_current_df = df[df[self.CURRENT_RAIL_COLUMN_HEADER] == False]

        no_current_df = self._update_valid_voltage_df_column(df=no_current_df)

        # Update Valid_Voltage spec_min column

        # Validate an "first rail" is in the list:
        firsts = df[df[self.POWER_ON_TIME_COLUMN_HEADER] == 0]
        if firsts.empty:
            # TODO:: What do we do with invalid dataframes?
            return pd.DataFrame()
        else:
            return no_current_df

    def _determine_first_rail(self, waveform_list: t.List[
        WaveformEntity]) -> WaveformEntity:
        first_wf = None
        first_ss = np.inf

        for wf in waveform_list:
            if not wf.edge:
                continue
            steady_ss = wf.steady_state_index()

            # Remove all rails that are already up when the capture started
            # and
            # See if steady state is earlier or not
            if steady_ss > 5 and steady_ss < first_ss:
                first_wf = wf
                first_ss = steady_ss

        return first_wf

    def _determine_power_on_time(self, waveform: WaveformEntity,
                                 valid_voltage: float = None) -> \
            t.Tuple[float, int]:
        try:
            t0_index = waveform.steady_state_index(
                expected_voltage=valid_voltage)
            t0 = waveform.x_axis_in_milliseconds()[t0_index]
        except TypeError as e:
            raise (f"Waveform TypeError. Was a current waveform "
                   f"mislabeled?\n\n {e}")
        return t0, t0_index

    def _determine_t0(self, df: pd.DataFrame, waveform_list: t.List[
        WaveformEntity]) -> t.Tuple[float, int]:
        '''
        Takes in a dataframe and determines when the first edge rail has
        fully ramped.  The first edge rail ramp is considered t0.

        @param waveform_list:  A list of waveform Entities
        @df: A dataframe with the index being testpoint names
        @return:
        '''

        first_edge_rail = self._determine_first_rail(
            waveform_list=waveform_list)
        if first_edge_rail is None:
            # TODO:: What do we do if there isn't an edge rail first???
            return -1, 0  # ERROR?
        valid_voltage = df.at[first_edge_rail.testpoint, "valid_voltage"]

        t0, t0_index = self._determine_power_on_time(
            waveform=first_edge_rail, valid_voltage=valid_voltage)

        return t0, t0_index

    def update_df_with_t0_and_timing(self, df: pd.DataFrame) -> pd.DataFrame:
        wf_df = df.set_index("testpoint")
        wfms = self.load_waveforms_by_df(df=df)
        t0, t0_index = self._determine_t0(df=wf_df, waveform_list=wfms)

        df[self.CAPTURE_RAMP_T0] = t0
        df[self.CAPTURE_T0_INDEX] = t0_index

        for waveform in wfms:
            valid_voltage = wf_df.at[waveform.testpoint, "valid_voltage"]
            poweron_time, poweron_index = self._determine_power_on_time(
                waveform=waveform, valid_voltage=valid_voltage)
            # Adjust power-on Time to remove t0
            t0_to_ramp = poweron_time - t0

            # Update the dataframe
            df.loc[df.testpoint == waveform.testpoint,
                   self.RAIL_POWERON_FROM_T0] = t0_to_ramp
            df.loc[df.testpoint == waveform.testpoint,
                   self.TOTAL_POWERON_TIME] = poweron_time
            df.loc[df.testpoint == waveform.testpoint,
                   self.POWERON_INDEX] = poweron_index
        return df
