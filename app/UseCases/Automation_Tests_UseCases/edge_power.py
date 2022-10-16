from __future__ import annotations
import typing as t

import pandas as pd
from collections import OrderedDict

from app.UseCases.Automation_Tests_UseCases.automation_test_usecase import \
    AutomationTestUseCase, AutomationTestRequestObject
from app.shared.Responses.response import Response, ResponseSuccess
from app.UseCases.Post_Processing_UseCases.ramp_processing \
    .validate_ramp_use_case import RampProcessingUseCase
from app.UseCases.Post_Processing_UseCases.Overshoot_undershoot_processing \
    .over_under_shoot_use_case import OverUnderShootProcessingUseCase
from app.UseCases.Post_Processing_UseCases.waveform_min_max_processing \
    .min_max_use_case import WaveformProcessingUseCase, \
    PostProcessingRequestObject

from app.UseCases.Post_Processing_UseCases.waveform_min_max_processing \
    .waveform_min_max_use_case import TestpointMinMaxProcessingUseCase, \
    MinMaxRequestObject


class EdgePowerUseCase(AutomationTestUseCase):
    _name = "EdgePower"
    LAST_FILTERBY: str = "datacapture_id"

    def process_request(self,
                        request_object: AutomationTestRequestObject) -> Response:
        """
        Need to write this code! The code below is stolen from VSD
        """
        # Last filterby is "testpoint", so default is one above that, capture
        groupby_list = self.set_filter_by_list(
            filter_by=request_object.filter_by,
            what_default="capture")
        '''

        if (request_object.filter_by == "default") or (
                request_object.filter_by == self.LAST_FILTERBY):
            plot_individual = True
        else:
            plot_individual = False

        groupby_without_testpoint = groupby_list[:-1]

        min_max_df = pd.DataFrame()
        entity_dict = OrderedDict()
        feature_dict = OrderedDict()
        for filters, group_df in request_object.df.groupby(by=groupby_list):
            # Remove Testpoint from filters
            filters = filters[:-1]
            entity_dict = self.process_filter_entities(filter_tuple=filters,
                                                       groupby_list=groupby_without_testpoint,
                                                       entity_dict=entity_dict)

            actual_filters = tuple(
                entity.descriptor for entity in entity_dict.values())

            min_max_req = MinMaxRequestObject(df=group_df,
                                              plot_individual=plot_individual,
                                              filter_tuple=actual_filters)

            min_max_uc = TestpointMinMaxProcessingUseCase(repo=self.repo)
            min_max_resp = min_max_uc.execute(request_object=min_max_req)

            combined_df = self.combine_filters_with_results(
                entity_dict=entity_dict, feature_dict=feature_dict,
                response=min_max_resp)
            # Will return empty if the waveform is an edge rail
            if not combined_df.empty:
                min_max_df = pd.concat([min_max_df, combined_df],
                                       ignore_index=True)
            # 1) Validate Voltage Ramp
            ramp_resp = RampProcessingUseCase(repo=self.repo).execute(
                request_object=pp_req)
            ramp_sheet, ramp_df = ramp_resp.value

            # 2) Validate Voltage Overshoot/Undershoot
            shoot_resp = OverUnderShootProcessingUseCase(repo=self.repo).execute(
                request_object=pp_req)
            shoot_sheet, shoot_df = shoot_resp.value

            # 3) Validate Steady State Voltage Min/Max
            voltage_resp = WaveformProcessingUseCase(repo=self.repo).execute(
                request_object=pp_req)
            voltage_sheet, voltage_df = voltage_resp.value

            final_data_dict = OrderedDict([
                (ramp_sheet, ramp_df),
                (shoot_sheet, shoot_df),
                (voltage_sheet, voltage_df),
            ])

        data_dict = OrderedDict([
            ("VSD", min_max_df)
        ])

        excel_path_str = self.build_excel_file(data_dict=data_dict)
        return ResponseSuccess(value=excel_path_str)
        '''
        raise NotImplementedError

    def _build_excel_file(self, output_path: pd.ExcelWriter,
                          data_dict: t.OrderedDict[
                              str, pd.DataFrame]) -> None:
        """

        @param output_path:  pd.ExcelWriter
        @return: path to excel writer

        """

        for sheet_name, df in data_dict.items():
            df.to_excel(excel_writer=output_path, startrow=0, merge_cells=False,
                        sheet_name=sheet_name)
