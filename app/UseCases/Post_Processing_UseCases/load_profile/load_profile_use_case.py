from __future__ import annotations

import typing as t
import pandas as pd
import numpy as np

from app.UseCases.Automation_Test_Post_Processing.post_processing_usecase import AutomationTestUseCase
from app.shared.Requests.requests import ValidRequestObject
from app.shared.Responses.response import Response, ResponseSuccess
from app.shared.Results.results import ScopePowerResult
from app.shared.Entities.entities import WaveformEntity


class LoadProfileRequestObject(ValidRequestObject):
    df: pd.DataFrame
    max_power: float

    def __init__(self, df: pd.DataFrame, max_power):
        assert isinstance(df, pd.DataFrame)
        self.df = df
        self.max_power = max_power

    @classmethod
    def from_dict(cls, adict) -> LoadProfileRequestObject:
        return cls(**adict)


class LoadProfileUseCase(AutomationTestUseCase):
    by: t.List[str] = ["dut"]

    def process_request(self,
                        request_object: LoadProfileRequestObject) -> Response:
        '''
        The Load Profile test has to do 3 main functions for each capture:
            - Validate current never exceeds the maximum value
            - Validate power never exceeds the maximum value
            - Validate waveform_names are stable/within spec during the entire test
        '''
        # result_dict = self.fake_process_request(df=request_object.df)
        # result = [("fake_sheet", result_dict)]
        # return ResponseSuccess(result)

        capture_groups = self.groupby_capture(df=request_object.df)
        current_results = []
        waveform_results = []
        power_result = ScopePowerResult()
        for i, group_dict in enumerate(capture_groups):
            group_df = group_dict['df']
            group_wfs = self.load_waveforms(df=group_df)

            '''
            validated_current_results = self.validate_current(
                waveform_names=group_wfs, df=group_df)
            '''

            validated_power = self.validate_power(df=group_dict["df"],
                                                  waveforms=group_wfs)

            validated_waveforms = self.validate_waveforms(df=group_dict["df"],
                                                          waveforms=group_wfs)

            for power_ent in validated_power:
                if power_ent.steady_state_max < request_object.max_power:
                    result = "Pass"
                    result_reason = ""
                else:
                    result= "Fail"
                    result_reason = f"{request_object.max_power} exceeded \n" \
                                    f"({power_ent.steady_state_max} >= " \
                                    f"{request_object.max_power})"
                power_result.add_result(power_entity=power_ent,
                                        df_row=group_df.iloc[0],
                                        picture_location="",
                                        result=result,
                                        result_rationale = result_reason)

            #current_results = current_results + validated_current_results
            waveform_results = waveform_results + validated_waveforms

        final_result = {
            power_result.sheet_name: power_result.df.to_dict(),
            "waveform": waveform_results,
        }

        return ResponseSuccess(value=final_result)

    def validate_power(self, waveforms: t.List[WaveformEntity],
                       df: pd.DataFrame) -> t.List[WaveformEntity]:
        result_list = []
        edge_pairs = self.return_edge_rail_pairs(waveform_list=waveforms)

        for volt_wf, curr_wf in edge_pairs:
            power_ent = self.create_power_entity(volt_wf=volt_wf,
                                                 curr_wf=curr_wf)

            #power_dict = power_ent.to_dict()
            #power_dict.pop('downsample')
            result_list.append(power_ent)
        return result_list

    def validate_waveforms(self, waveforms: t.List[WaveformEntity],
                           df: pd.DataFrame) -> t.List[dict]:

        result = []
        for i, row in df.iterrows():
            waveform = [wf for wf in waveforms
                        if wf._id == self._waveform_id_from_row(row)][0]
            spec_max = self._spec_max_from_row(row)
            spec_min = self._spec_min_from_row(row)
            expected_nom = self._expected_nominal_from_row(row)

            r = waveform.to_dict()
            r.pop('downsample')
            r['spec_max'] = spec_max
            r['spec_min'] = spec_min
            r['expected_nominal'] = expected_nom

            result.append(r)
        return result

    def find_minimum_steady_state_index(self, waveform_list: t.List[
        WaveformEntity]) -> int:

        index_list = []
        for wf in waveform_list:
            if wf.units == "A":
                continue  ## Steady State Index is not set for current rails,
                # will return 0
            index_list.append(wf.steady_state_index())
        return min(index_list)

    '''

    def validate_current(self, waveform_names: t.List[WaveformEntity],
                         df: pd.DataFrame) -> t.List[dict]:
        edge_pairs = self.return_edge_rail_pairs(waveform_list=waveform_names)

        min_ss_index = self.find_minimum_steady_state_index(
            waveform_list=waveform_names)
        result_list = []

        for volt_wf, curr_wf in edge_pairs:
            result = {}

            curr_ss_index = min_ss_index + 5
            curr_max_ss = np.max(curr_wf.y_axis()[curr_ss_index:])
            curr_max = np.max(curr_wf.y_axis())
            spec_max = self._spec_max_from_waveform_id(
                df=df, waveform_id=curr_wf._id)

            if curr_max < spec_max:
                result["Result"] = "Pass"
                result['Reason'] = ""
            elif curr_max_ss < spec_max:
                if min_ss_index < volt_wf.steady_state_index():
                    result['Result'] = "Review Me!"
                    result['Reason'] = f"Minimum steady state came before " \
                                       f"{volt_wf.testpoint} rail steady state"
                else:
                    result['Result'] = "Pass"
                    result['Reason'] = ""
            else:
                result["Result"] = "Fail"
                result['Reason'] = f"Spec Max [{spec_max}] exceeded by max " \
                                   f"current [{curr_max_ss}]"
            result['max_current_ss'] = curr_max_ss
            result['max_current'] = curr_max
            result['mean_current_ss'] = np.mean(curr_wf.y_axis())
            result['min_current_ss'] = np.min(curr_wf.y_axis())
            result_list.append(result)
        return result_list

    def _validate_current(self, row_dict: pd.Series):
        wf_id = self._waveform_id_from_row(df_row=row_dict)
        wf = self.return_wf(waveform_id=wf_id)
        spec_max = self._spec_max_from_row(df_row=row_dict)
        if wf.steady_state_max >= spec_max:
            row_dict["Result"] = "Fail"
            row_dict['Reason'] = f"Spec Max [{spec_max}] exceeded by max current [" \
                            f"{wf.steady_state_max}]"
        else:
            row_dict['Result'] = "Pass"
            row_dict['Reason'] = ""
    '''

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
        Returns a list of tuples containing (voltage, current) waveform_names.
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


