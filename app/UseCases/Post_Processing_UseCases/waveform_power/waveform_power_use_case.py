import typing as t

import pandas as pd
import numpy as np

from ..post_processing_use_case import PostProcessingRequestObject, \
    PostProcessingUseCase

from app.shared.Entities.entities import WaveformEntity


class WaveformEdgePowerUseCase(PostProcessingUseCase):
    sheet_name = "Waveform Edge Power"

    def post_process(self, request_object: PostProcessingRequestObject) -> \
            pd.DataFrame:
        """
        The Waveform Edge Power test validates the power never
        exceeds the spec max power level.
            - Validate power never exceeds the maximum value

        @param request_object:
        @return:
        """
        #resultEntity = Power

        capture_groups = request_object.df.groupby(by=["runid", "capture"])

        for (runid, capture), capture_df in capture_groups:
            wfs = self.load_waveforms_by_df(df=capture_df)

            edge_pairs = self.return_edge_rail_pairs(waveform_list=wfs)

            for volt_wf, current_wf in edge_pairs:
                power_ent = self.create_power_entity(volt_wf=volt_wf,
                                                     curr_wf=current_wf)
                row = self._row_from_waveform_id(df=capture_df,
                                                 waveform_id=current_wf._id)
                spec_max_power = self._max_power_from_row(df_row=row)

                result = self.generate_result(power_entity=power_ent,
                                              max_power=spec_max_power)

                print(result)

    def generate_result(self, power_entity, max_power):
        result = "Invalid"
        result_reason = "Code didn't run correctly...?"
        if power_entity.max < max_power:
            result = "Pass"
            result_reason = ""
        elif power_entity.steady_state_max < max_power:
            result = "Pass"
            result_reason = \
                f"{max_power}{power_entity.units} < steady state [" \
                f"{power_entity.steady_state_max}{power_entity.units}]," \
                f"although max [{power_entity.max}{power_entity.units}] " \
                f"exceeds the limit"
        else:
            result = "Fail"
            result_reason = f"{max_power} exceeded \n" \
                            f"({power_entity.steady_state_max} >= " \
                            f"{max_power})"

        return {"Result": result,
                "Reason": result_reason}

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
