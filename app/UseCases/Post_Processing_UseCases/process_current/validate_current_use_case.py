from __future__ import annotations

import os
import typing as t
import pandas as pd
import numpy as np
from pathlib import Path

from app.UseCases.Post_Processing_UseCases.post_processing_use_case import \
    PostProcessingRequestObject, PostProcessingUseCase
from app.shared.Requests.requests import ValidRequestObject
from app.shared.Responses.response import Response, ResponseSuccess
from app.shared.Entities.entities import WaveformEntity
from app.UseCases.Post_Processing_UseCases.process_current \
    .validate_current_results import CurrentProcessingResultEntity, \
    CurrentProcessResultRow


class CurrentProcessingUseCase(PostProcessingUseCase):
    _file_prefix:str = "CurrentProcessing"
    sheet_name = "Current Waveforms"
    result_entity = CurrentProcessingResultEntity(sheet_name=sheet_name)
    """ The minimum steady state index is
      # buffered so the capacitive inrush is not considered. """
    STEADY_STATE_INRUSH_BUFFER = 5

    def post_process(self, request_object: PostProcessingRequestObject) -> \
            pd.DataFrame:
        """
        The Current Processing Test validates the current never exceeds the
        spec max current.
            - Validate current never exceeds the maximum value

        @param request_object: 
        @return: 
        """

        current_wf_list = self.update_current_waveform_by_capture(
            df=request_object.df)

        result_df = pd.DataFrame()

        for current_wf in current_wf_list:
            row = self._row_from_waveform_id(df=request_object.df,
                                             waveform_id=current_wf._id)
            result = self.validate_current_waveform(current_wf=current_wf,
                                                    df_row=row)

            file_path = Path(r"C:\Users\ammonk\OneDrive - Intel "
                             r"Corporation\Desktop\Test_Folder\fake_uploads\fake_results")
            file_path = file_path.joinpath(current_wf._id)
            image_str = str(file_path.resolve())
            result_row = CurrentProcessResultRow.from_dataframe_row(
                row=row,
                curr_wf=current_wf,
                result=result["Result"],
                result_reason=result["Reason"],
                image_str=image_str)
            result_row.plot_waveforms(output_path=file_path,
                                      waveforms=[current_wf])
            d = result_row.to_result()
            if result_df.empty:
                result_df = pd.DataFrame(d, columns=list(d.keys()), index=[0])
            else:
                s = pd.Series(d)
                result_df = result_df.append(s, ignore_index=True)

        return result_df

    def update_current_waveform_by_capture(self, df: pd.DataFrame) -> t.List[
        WaveformEntity]:
        """

        @param df:
        @return:
        """
        current_waveforms = []

        capture_groups = df.groupby(by=['runid', 'capture'])

        for (runid, capture), capture_df in capture_groups:
            wfs = self.load_waveforms_by_df(df=capture_df)

            capture_current_wfs = self.update_current_rails(wf_list=wfs)
            current_waveforms.extend(capture_current_wfs)

        return current_waveforms

    def update_current_rails(self, wf_list: t.List[WaveformEntity]) -> \
            t.List[WaveformEntity]:
        """

        @return:
        """
        current_rails = []
        edge_pairs = self.return_edge_rail_pairs(waveform_list=wf_list)

        earliest_ss_index = self.waveform_list_minimum_steady_state_index(
            wf_list)

        for volt_wf, curr_wf in edge_pairs:
            curr_wf_ss_index = earliest_ss_index + self.STEADY_STATE_INRUSH_BUFFER

            current_wf = self.update_current_wf(current_wf=curr_wf,
                                                associated_rail_ss_index=
                                                volt_wf.steady_state_index(),
                                                steady_state_index=
                                                curr_wf_ss_index)
            current_rails.append(current_wf)
        return current_rails

    def update_current_wf(self, current_wf: WaveformEntity,
                          associated_rail_ss_index: int,
                          steady_state_index) -> WaveformEntity:
        """

        @param current_wf:
        @param associated_rail_ss_index:
        @param steady_state_index:
        @return:
        """
        curr_wf_ss = current_wf.y_axis()[steady_state_index:]

        current_wf.steady_state_max = np.max(curr_wf_ss)
        current_wf.steady_state_min = np.min(curr_wf_ss)
        current_wf.steady_state_mean = np.mean(curr_wf_ss)
        current_wf.steady_state_pk2pk = np.ptp(curr_wf_ss)
        current_wf.associated_rail_ss_index = associated_rail_ss_index

        return current_wf

    def validate_current_waveform(self, current_wf: WaveformEntity,
                                  df_row: pd.Series) -> t.Dict[str, str]:
        """

        @param current_wf:
        @param df_row:
        @return:
        """
        result_d = {
            "Result": "Invalid",
            "Reason": "The code ran incorrectly...?"
        }

        spec_max = self._spec_max_from_row(df_row=df_row)

        if current_wf.max < spec_max:
            result_d["Result"] = "Pass"
            result_d["Reason"] = \
                f"Max current [{current_wf.max}{current_wf.units}] < " \
                f"Spec Max[{spec_max}]"
        elif current_wf.steady_state_max < spec_max:
            if current_wf.steady_state_index() < current_wf.associated_rail_ss_index:
                result_d["Result"] = "Review Me!"
                result_d["Reason"] = f"Minimum steady state came before " \
                                     f"{current_wf.associated_rail} rail steady state"
            else:
                result_d["Result"] = "Pass"
                result_d['Reason'] = f"non-capacitive Inrush < {spec_max}, " \
                                     f"although capacitive inrush was higher " \
                                     f"[{current_wf.max}{current_wf.units}]"
        elif current_wf.steady_state_max >= spec_max:
            result_d["Result"] = "Fail"
            result_d[
                "Reason"] = f"Spec Max [{spec_max}{current_wf.units}] " \
                            f"exceeded by max current " \
                            f"[{current_wf.steady_state_max}{current_wf.units}]"

        return result_d

    '''
    if validated_current_results_list:
        ccpr = validated_current_results_list[0]
    image_location = ccpr.plot_waveforms(output_path=image_path,
                                         waveform_names=group_wfs)
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

    return result_df
    '''


'''
def validate_current(self, waveform_names: t.List[WaveformEntity],
                     row_dict: pd.Series) -> t.List[CurrentProcessResultRow]:
    # TODO:: this code is assuming only 1 edge edge_pair, although there could
    # be 2 or more. Need to fix the for loop.
    result_list = []
    edge_pairs = self.return_edge_rail_pairs(waveform_list=waveform_names)

    min_ss_index = self.waveform_list_minimum_steady_state_index(
        waveform_list=waveform_names)

    for volt_wf, curr_wf in edge_pairs:
        result = "Invalid"
        result_reason = "The code ran incorrectly...?"

        spec_max = row_dict['spec_max']
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

        cprr = CurrentProcessResultRow.from_dataframe_row(row_dict, curr_wf,
                                                          result,
                                                          result_reason,
                                                          image_str="")
        result_list.append(cprr)
    return result_list

def _validate_current(self, row_dict: pd.Series):
    wf_id = self._waveform_id_from_row(df_row=row_dict)
    wf = self.return_wf(waveform_id=wf_id)
    spec_max = wf.spec_max
    if spec_max is None:
        row_dict["Result"] = "Invalid"
        row_dict["Reason"] = "Specification Not Applied"
    elif wf.steady_state_max < spec_max:
        row_dict['Result'] = "Pass"
        row_dict['Reason'] = ""
    else:
        row_dict["Result"] = "Fail"
        row_dict['Reason'] = f"Spec Max [{spec_max}{wf.units}] exceeded by max " \
                        f"current [{wf.steady_state_max}{wf.units}]"

@classmethod
def _fake_rail_from_current(cls,
                            current_rail: WaveformEntity) \
        -> WaveformEntity:
    testpoint = f"{current_rail.testpoint} Missing Voltage Rail"
    downsample_x = current_rail.downsample[0]
    downsample_y = np.zeros(len(downsample_x)).tolist()
    downsample = [downsample_x, downsample_y]

    fake_entity = cls._create_fake_edge_rail(testpoint=testpoint,
                                             runid=current_rail.runid,
                                             capture=current_rail.capture,
                                             test_category=current_rail.test_category,
                                             downsample=downsample,
                                             associated_rail=current_rail.testpoint)
    return fake_entity
'''
