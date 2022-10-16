from __future__ import annotations

import typing as t
import pandas as pd
import numpy as np
from pathlib import Path

from flask import current_app

from app.UseCases.post_processing_tests.post_processing_usecase import \
    PostProcessingWaveFormUseCase
from app.shared.Requests.requests import ValidRequestObject
from app.shared.Responses.responses import Response, ResponseSuccess
from app.shared.Entities.entities import WaveformEntity
from app.UseCases.post_processing_tests.process_current\
    .validate_current_results import CurrentProcessResultRow


class CurrentProcessingRequestObject(ValidRequestObject):
    df: pd.DataFrame

    def __init__(self, df: pd.DataFrame):
        assert isinstance(df, pd.DataFrame)
        self.df = df

    @classmethod
    def from_dict(cls, adict) -> CurrentProcessingRequestObject:
        return cls(**adict)


class CurrentProcessingUseCase(PostProcessingWaveFormUseCase):
    sheet_name = "Current Waveforms"

    def process_request(self,
                        request_object: CurrentProcessingRequestObject) -> Response:
        '''
        The Current Processing Test validates the current never exceeds the
        spec max current.
            - Validate current never exceeds the maximum value
        '''
        capture_groups = self.groupby_capture(request_object.df)
        result_df = pd.DataFrame()
        image_path = Path(current_app.config['RESULTS_FOLDER'])

        for i, group_dict in enumerate(capture_groups):
            group_df = group_dict['df']
            group_wfs = self.load_waveforms(df=group_df)

            current_rows = group_df[group_df["current_rail"]]

            for i, row in current_rows.iterrows():
                validated_current_results_list = self.validate_current(
                    waveforms=group_wfs, row=row)

                if validated_current_results_list:
                    ccpr = validated_current_results_list[0]
                    image_location = ccpr.plot_waveforms(
                        output_path=image_path, waveforms=group_wfs)
                    for ccpr in validated_current_results_list:
                        ccpr.image_location = image_location
                        result_row = ccpr.to_result()
                        if result_df.empty:
                            cols = list(result_row.keys())
                            result_df = pd.DataFrame(
                                result_row, columns=cols, index=[0])
                        else:
                            result_row = pd.Series(result_row)
                            result_df = result_df.append(result_row,
                                                             ignore_index=True)

        return ResponseSuccess(value={self.sheet_name: result_df})

    def find_minimum_steady_state_index(self, waveform_list: t.List[
        WaveformEntity]) -> int:

        index_list = []
        for wf in waveform_list:
            if wf.units == "A":
                continue  ## Steady State Index is not set for current rails,
                # will return 0
            index_list.append(wf.steady_state_index())
        return min(index_list)

    def validate_current(self, waveforms: t.List[WaveformEntity],
                         row: pd.Series) -> t.List[CurrentProcessResultRow]:
        #TODO:: this code is assuming only 1 edge pair, although there could
        # be 2 or more. Need to fix the for loop.
        result_list = []
        edge_pairs = self.return_edge_rail_pairs(waveform_list=waveforms)

        min_ss_index = self.find_minimum_steady_state_index(
            waveform_list=waveforms)

        for volt_wf, curr_wf in edge_pairs:
            result = "Invalid"
            result_reason = "The code ran incorrectly...?"

            spec_max = row['spec_max']
            curr_ss_index = min_ss_index + 5
            curr_wf_ss = curr_wf.y_axis()[curr_ss_index:]

            curr_wf.steady_state_max = np.max(curr_wf_ss)
            curr_wf.steady_state_min = np.min(curr_wf_ss)
            curr_wf.steady_state_mean = np.mean(curr_wf_ss)
            curr_wf.steady_state_pk2pk = np.ptp(curr_wf_ss)

            if curr_wf.max < spec_max:
                result = "Pass"
                result_reason = ""
            elif curr_wf.steady_state_max < spec_max:
                if min_ss_index < volt_wf.steady_state_index():
                    result = "Review Me!"
                    result_reason = f"Minimum steady state came before " \
                                       f"{volt_wf.testpoint} rail steady state"
                else:
                    result = "Pass"
                    result_reason = f"non-capacitive Inrush < {spec_max}, " \
                                    f"although capacitive inrush was higher"
            elif curr_wf.steady_state_max >= spec_max:
                result = "Fail"
                result_reason = f"Spec Max [{spec_max}] exceeded by max " \
                                   f"current [{curr_wf.steady_state_max}]"

            cprr = CurrentProcessResultRow.from_dataframe_row(row, curr_wf,
                                                            result,
                                                       result_reason,
                                                              image_str="")
            result_list.append(cprr)
        return result_list

    def _validate_current(self, row: pd.Series):
        wf_id = self._waveform_id_from_row(df_row=row)
        wf = self.return_wf(waveform_id=wf_id)
        spec_max = self._spec_max_from_row(df_row=row)
        if wf.steady_state_max >= spec_max:
            row["Result"] = "Fail"
            row['Reason'] = f"Spec Max [{spec_max}] exceeded by max current [" \
                            f"{wf.steady_state_max}]"
        else:
            row['Result'] = "Pass"
            row['Reason'] = ""

    def load_waveforms(self, df: pd.DataFrame) -> t.List[WaveformEntity]:
        wf_ids = df["WaveformEntity_id"].values
        filter_list = [{"_id": id} for id in wf_ids]
        wf_dicts = self.repo.find_many_waveforms(list_of_filters=filter_list)
        wf_entities = [WaveformEntity.from_dict(wf_dict) for wf_dict in
                       wf_dicts]
        return wf_entities

    def _waveform_id_from_row(self, df_row: pd.Series) -> str:
        wf_id = df_row["WaveformEntity_id"]
        return wf_id

    def _spec_max_from_waveform_id(self, df: pd.DataFrame, waveform_id: str):
        wf_df = df[df["WaveformEntity_id"] == waveform_id]
        spec = wf_df.iloc[0]["spec_max"]
        return spec

    def _spec_max_from_row(self, df_row: pd.Series) -> float:
        spec = df_row['spec_max']
        return spec

    def _spec_min_from_row(self, df_row: pd.Series) -> float:
        spec = df_row['spec_min']
        return spec

    def _expected_nominal_from_row(self, df_row: pd.Series) -> float:
        spec = df_row['expected_nominal']
        return spec

    def return_wf(self, waveform_id) -> WaveformEntity:
        wf_dict = self.repo.find_waveform_by_id(waveform_id=waveform_id)
        wf = WaveformEntity.from_dict(wf_dict)
        return wf

    def _return_rails_by_edge(self, df: pd.DataFrame,
                              edge: bool = False) -> list:
        rails = []
        for i, row in df[df['edge_rail'] == edge].iterrows():
            wf_id = row['WaveformEntity_id']
            wf = self.return_wf(waveform_id=wf_id)
            rails.append(wf)
        return rails

    def _return_rails(self, df: pd.DataFrame) -> t.List[WaveformEntity]:
        wf_ids = df["WaveformEntity_id"].values
        filters = [{"_id": wf_id} for wf_id in wf_ids]
        rails = self.repo.find_many_waveforms(filters=filters)
        wfs = [WaveformEntity.from_dict(adict=wf_dict) for wf_dict in rails]
        return wfs

    @classmethod
    def _fake_rail_from_current(cls,
                                current_rail: WaveformEntity) \
            -> WaveformEntity:
        testpoint = f"{current_rail.testpoint} Missing Voltage Rail"
        downsample_x = current_rail.downsample[0]
        downsample_y = np.zeros(len(downsample_x)).tolist()
        downsample = [downsample_x, downsample_y]

        fake = cls._create_fake_edge_rail(testpoint=testpoint,
                                          runid=current_rail.runid,
                                          capture=current_rail.capture,
                                          test_category=current_rail.test_category,
                                          downsample=downsample,
                                          associated_rail=current_rail.testpoint)
        return fake

    @classmethod
    def _create_fake_edge_rail(cls, testpoint: str, runid: int, capture: int,
                               test_category: str, downsample: list,
                               associated_rail: str, units: str = "V",
                               location: str = "N/A", scope_channel=99) \
            -> WaveformEntity:
        v_wf = WaveformEntity(testpoint=testpoint,
                              runid=runid,
                              capture=capture,
                              test_category=test_category,
                              units=units,
                              location=location, scope_channel=scope_channel,
                              downsample=downsample,
                              edge=True, associated_rail=associated_rail)
        return v_wf

    @classmethod
    def _pair_voltage_to_current(cls, edges: t.List[WaveformEntity]) -> \
            t.List[t.Tuple[WaveformEntity, WaveformEntity]]:
        '''
        Returns a list of tuples containing (voltage, current) waveforms.
        '''
        volt_list = [wf for wf in edges if wf.units == "V"]
        current_list = [wf for wf in edges if wf.units == "A"]
        result = []
        for c_wf in current_list:
            v_wf = [v for v in volt_list if v.testpoint == c_wf.associated_rail]
            if not v_wf:
                v_wf = cls._fake_rail_from_current(current_rail=c_wf)
            else:
                v_wf = v_wf[0]

            result.append((v_wf, c_wf))

        return result

    def return_edge_rail_pairs(self, waveform_list: t.List[WaveformEntity]) -> \
            t.List[t.Tuple[WaveformEntity, WaveformEntity]]:
        edges = [wf for wf in waveform_list if wf.edge]
        return self._pair_voltage_to_current(edges=edges)

    def return_edge_rail_pairs_df(self, df: pd.DataFrame) -> t.List[
        t.Tuple[WaveformEntity, WaveformEntity]]:
        ''' Takes in a dataframe and turns it into edge wf tuples '''

        edges = self._return_edge_waveforms(df=df)
        return self._pair_voltage_to_current(edges=edges)

    def _calculate_power(self, volt_wf: WaveformEntity,
                         curr_wf: WaveformEntity) -> np.array:
        volt = np.array(volt_wf.downsample[1])
        curr = np.array(curr_wf.downsample[1])
        power = volt * curr
        return power

    def create_power_entity(self, volt_wf: WaveformEntity,
                            curr_wf: WaveformEntity):
        power_y_array = self._calculate_power(volt_wf=volt_wf, curr_wf=curr_wf)
        power_x_array = np.array(curr_wf.x_axis())
        power_downsample = [power_x_array, power_y_array]
        ss_index = volt_wf.steady_state_index() + 5

        power_entity = self._create_power_entity(runid=volt_wf.runid,
                                                 capture=volt_wf.capture,
                                                 test_category=volt_wf.test_category,
                                                 associated_rail=volt_wf.testpoint,
                                                 downsample=power_downsample,
                                                 ss_index=ss_index)

        return power_entity

    def _create_power_entity(self, runid: int, capture: int,
                             test_category: str, associated_rail: str,
                             downsample: t.List[np.ndarray], ss_index: int) -> \
            WaveformEntity:

        assert isinstance(downsample, list)
        testpoint = f"{associated_rail}_Power"

        ss_y = downsample[1][ss_index:]
        ss_pk2pk = ss_y.ptp()
        ss_mean = ss_y.mean()
        ss_min = ss_y.min()
        ss_max = ss_y.max()
        wf_max = downsample[1].max()
        wf_min = downsample[1].min()

        downsample = [downsample[0].tolist(), downsample[1].tolist()]

        power_entity = WaveformEntity(testpoint=testpoint,
                                      runid=runid,
                                      capture=capture,
                                      test_category=test_category,
                                      units="W",
                                      location="N/A",
                                      scope_channel=100,
                                      steady_state_pk2pk=ss_pk2pk,
                                      steady_state_max=ss_max,
                                      steady_state_mean=ss_mean,
                                      steady_state_min=ss_min,
                                      max=wf_max, min=wf_min,
                                      edge=True,
                                      associated_rail=associated_rail,
                                      downsample=downsample)

        return power_entity

    def _process_onboard_rails(self, df: pd.DataFrame):
        return None

    def _return_onboard_rails(self, df: pd.DataFrame) -> list:
        edge = False
        return self._return_rails_by_edge(df, edge)

    def _return_edge_waveforms(self, df: pd.DataFrame) -> list:
        edge = True
        return self._return_rails_by_edge(df, edge)

    def groupby_capture(self, df: pd.DataFrame) -> t.List[dict]:
        result = []
        by = ["dut", "pba", "rework", "serial_number", "runid",
              "capture"]
        capture_group = df.groupby(by=by)
        for filters, group_df in capture_group:
            results_dict = {}
            for key, value in zip(by, filters):
                results_dict[key] = value
            results_dict["df"] = group_df
            result.append(results_dict)
        return result


