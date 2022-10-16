from __future__ import annotations
import typing as t
from pathlib import Path

import pandas as pd
from collections import OrderedDict

from app.UseCases.Automation_Tests_UseCases.automation_test_usecase import \
    AutomationTestUseCase, AutomationTestRequestObject
from app.shared.Responses.response import Response, ResponseSuccess

from app.UseCases.Post_Processing_UseCases.waveform_sequencing.waveform_sequencing_use_case import \
    WaveformSequencingUseCase
from app.UseCases.Post_Processing_UseCases.current_inrush \
    .current_inrush_use_case import InrushRequestObject, TestpointInrushUseCase

from app.UseCases.Post_Processing_UseCases.capture_timing \
    .capture_timing_use_case import CaptureTimingRequestObject, \
    CaptureTimingUseCase

from app.shared.Entities import Entity

from app.UseCases.Post_Processing_UseCases.waveform_sequencing \
    .waveform_sequencing2_use_case import WaveformSequencingUseCase, \
    WaveformSequencingRequestObject

from app.shared.ExcelWriter.excel_formats import FormattingExcelDataFrame

TIMING_COL = "timing_ms"


class InrushUseCase(AutomationTestUseCase):
    _name = "Inrush"
    LAST_FILTERBY: str = "testpoint"

    def process_request(self,
                        request_object: AutomationTestRequestObject) -> Response:
        """
        @param request_object:
        @return:
        """

        """
        """
        inrush_result_df = pd.DataFrame()

        # timed_df = self.calculate_capture_timings(df=request_object.df)
        edge_df = request_object.df[request_object.df["edge_rail"]]

        if edge_df.empty:
            return inrush_result_df

        groupby_list = self.set_filter_by_list(
            filter_by=request_object.filter_by, what_default="capture")

        # Last Filterby is testpoint. This removes that for the entity dict.
        groupby_list_without_testpoint = groupby_list[:-1]

        entity_dict = OrderedDict()
        feature_dict = OrderedDict()

        for filters, group_df in edge_df.groupby(
                by=groupby_list_without_testpoint):
            # Remove testpoint filter
            # filters = filters[:-1]
            entity_dict = self.process_filter_entities(filter_tuple=filters,
                                                       groupby_list=groupby_list_without_testpoint,
                                                       entity_dict=entity_dict)

            actual_filters = tuple(entity.descriptor for entity in
                                   entity_dict.values())

            inrush_df = self.execute_use_cases(
                df=group_df,
                filter_tuple=actual_filters,
                entity_dict=entity_dict)
            inrush_result_df = pd.concat(
                [inrush_result_df, inrush_df])

        # Write DF to excel File
        data_dict = OrderedDict([
            ("Inrush", inrush_result_df),
        ])

        excel_path_str = self.build_excel_file(data_dict=data_dict)

        return ResponseSuccess(value=excel_path_str)

    def execute_use_cases(self, df: pd.DataFrame, filter_tuple: t.Tuple[
        t.Any], entity_dict: t.OrderedDict[str, Entity]) -> \
            t.OrderedDict[str, pd.DataFrame]:
        '''
        @param df:
        @param filter_by:
        @return:
        '''

        feature_dict = OrderedDict()

        inrush_df = pd.DataFrame()

        for slew_rate, slew_df in df.groupby(
                by="temperature_power_settings_json_power_supply_channels_slew_rate_1"):
            feature_dict["Slew Rate"] = str(slew_rate)
            x = [f for f in filter_tuple]
            x.append(str(slew_rate))
            slew_tuple = tuple(x)
            # slew_tuple = tuple([f for f in filter_tuple].append(slew_rate))
            # 1) Waveform Sequencing
            inrush_req = InrushRequestObject(df=slew_df,
                                             filter_tuple=slew_tuple)
            uc = TestpointInrushUseCase(repo=self.repo)
            inrush_resp = uc.execute(request_object=inrush_req)

            slew_resp_df = self.combine_filters_with_results(
                entity_dict=entity_dict,
                feature_dict=feature_dict,
                response=inrush_resp)

            inrush_df = pd.concat([inrush_df, slew_resp_df])

        return inrush_df

    def calculate_capture_timings(self, df: pd.DataFrame) -> pd.DataFrame:
        '''
        Generates the timing lists for each capture in the input dataframe.

        @param df: input dataframe from userinput
        @return: input dataframe with timing column added
        '''

        timing_req = CaptureTimingRequestObject(df=df)
        uc = CaptureTimingUseCase(repo=self.repo)
        resp = uc.execute(request_object=timing_req)

        sheetname, timing_df = resp.value

        return timing_df

    def _build_excel_file(self, output_path: pd.ExcelWriter,
                          data_dict: t.OrderedDict[str, pd.DataFrame]) -> Path:
        """

        @param output_path:  pd.ExcelWriter
        @return: path to excel writer

        """
        xlsx_formatter = InrushExcelFormatter(output_path=output_path)

        for sheet_name, df in data_dict.items():
            xlsx_formatter.write_sheet(sheetname=sheet_name, df=df)

        xlsx_formatter.save_excel()

        return output_path


class InrushExcelFormatter(FormattingExcelDataFrame):
    TEST_SPECIFIC_HEADERS = ['Power PassFail', "Current PassFail",
                             "Min PassFail",
                             "Max PassFail"]

    def __init__(self, output_path: Path):
        super(InrushExcelFormatter, self).__init__(
            output_path=output_path,
            test_specific_headers=self.TEST_SPECIFIC_HEADERS)

    def _testspecific_formatting(self, worksheet, column: int,
                                 first_row: int,
                                 last_row: int, value: str):
        if value in ["Power PassFail", "Current PassFail"]:
            worksheet.conditional_format(first_row=first_row,
                                         first_col=column,
                                         last_row=last_row,
                                         last_col=column,
                                         options={'type': 'cell',
                                                  'criteria': 'equal',
                                                  'value': '"Pass"',
                                                  'format': self.pass_format})
            worksheet.conditional_format(first_row, column, last_row,
                                         column,
                                         {'type': 'cell',
                                          'criteria': 'equal',
                                          'value': '"Fail"',
                                          'format': self.fail_format})
            worksheet.conditional_format(first_row, column, last_row,
                                         column,
                                         {'type': 'cell',
                                          'criteria': 'equal',
                                          'value': '"N/A"',
                                          'format': self.na_format})
            worksheet.conditional_format(first_row, column, last_row,
                                         column,
                                         {'type': 'cell',
                                          'criteria': 'equal',
                                          'value': '"Reviewed"',
                                          'format': self.review_format})
