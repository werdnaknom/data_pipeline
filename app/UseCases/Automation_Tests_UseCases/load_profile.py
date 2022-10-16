from __future__ import annotations
import typing as t
from pathlib import Path

import pandas as pd
from collections import OrderedDict

from app.UseCases.Automation_Tests_UseCases.automation_test_usecase import \
    AutomationTestUseCase, AutomationTestRequestObject
from app.shared.Responses.response import Response, ResponseSuccess

# from app.UseCases.Post_Processing_UseCases.process_current. \
#    validate_current_use_case import CurrentProcessingUseCase, \
#    PostProcessingRequestObject

from app.UseCases.Post_Processing_UseCases.process_current. \
    capture_current_use_case import CaptureCurrentRequestObject, \
    CaptureCurrentProcessingUseCase

from app.UseCases.Post_Processing_UseCases.load_profile. \
    capture_profile_use_case import CaptureProfileRequestObject, \
    CaptureProfileProcessingUseCase

from app.shared.ExcelWriter.excel_formats import FormattingExcelDataFrame


class LoadProfileUseCase(AutomationTestUseCase):
    _name = "LoadProfile"
    LAST_FILTERBY: str = "datacapture_id"

    def process_request(self,
                        request_object: AutomationTestRequestObject) -> Response:
        """
        The Load Profile test has to do 3 main functions for each capture:
            - Validate current never exceeds the maximum value
            - Validate power never exceeds the maximum value
            - Validate waveform_names are stable/within spec during the entire test

        @param request_object: Automation Test Request -->
            df: combined datacsv
            filter_by: flag to filter data by
        @return:
        """
        # LAST FILTERBY is "capture", so one step above that is the default,
        # "runid"
        groupby_list = self.set_filter_by_list(
            filter_by=request_object.filter_by,
            what_default="runid")

        if request_object.filter_by != "default":
            groupby_list = groupby_list[:-1]

        entity_dict = OrderedDict()
        feature_dict = OrderedDict()

        current_result_df = pd.DataFrame()
        load_profile_result_df = pd.DataFrame()

        for filters, group_df in request_object.df.groupby(by=groupby_list):
            # Build DF output file
            entity_dict = self.process_filter_entities(filter_tuple=filters,
                                                       groupby_list=groupby_list,
                                                       entity_dict=entity_dict)

            actual_filters = tuple(
                entity.descriptor for entity in entity_dict.values())
            # Grabs pass/fail results and plots

            current_df, load_profile_df = self.execute_use_cases(
                df=group_df,
                filter_tuple=actual_filters,
                entity_dict=entity_dict)
            current_result_df = pd.concat([current_result_df, current_df],
                                          ignore_index=True)
            load_profile_result_df = pd.concat([load_profile_result_df,
                                                load_profile_df])

        # Writes DF to excel file
        data_dict = OrderedDict([
            ("Power&Current", current_result_df),
            ("Load Profile", load_profile_result_df)
        ])

        excel_path_str = self.build_excel_file(data_dict=data_dict)

        return ResponseSuccess(value=excel_path_str)

    def execute_use_cases(self, df: pd.DataFrame, filter_tuple: t.Tuple[t.Any],
                          entity_dict: t.OrderedDict[str, Entity],
                          ) -> t.Tuple[pd.DataFrame, pd.DataFrame]:
        '''
        @param df:
        @param filter_tuple:
        @param entity_dict:
        @return:
        '''
        feature_dict = OrderedDict()
        ''' CAPTURE CURRENT/POWER ANALYSIS'''
        current_req = CaptureCurrentRequestObject(df=df,
                                                  filter_tuple=filter_tuple)
        current_uc = CaptureCurrentProcessingUseCase(repo=self.repo)
        current_resp = current_uc.execute(request_object=current_req)

        current_df = self.combine_filters_with_results(entity_dict=entity_dict,
                                                       feature_dict=feature_dict,
                                                       response=current_resp)

        ''' CAPTURE VOLTAGE WAVEFORM ANALYSIS '''
        load_req = CaptureProfileRequestObject(df=df,
                                               filter_tuple=filter_tuple)

        load_uc = CaptureProfileProcessingUseCase(repo=self.repo)
        load_resp = load_uc.execute(request_object=load_req)

        load_df = self.combine_filters_with_results(entity_dict=entity_dict,
                                                    feature_dict=feature_dict,
                                                    response=load_resp)

        return current_df, load_df

    def _build_excel_file(self, output_path: Path,
                          data_dict: t.OrderedDict[
                              str, pd.DataFrame]) -> str:
        """

        @param output_path:  Path
        @return: path to excel writer

        """
        xlsx_formatter = LoadProfileExcelFormatter(output_path=output_path)

        for sheet_name, df in data_dict.items():
            xlsx_formatter.write_sheet(sheetname=sheet_name, df=df)

        xlsx_formatter.save_excel()

        return output_path


class LoadProfileExcelFormatter(FormattingExcelDataFrame):
    TEST_SPECIFIC_HEADERS = ['Power PassFail', "Current PassFail",
                             "Min PassFail",
                             "Max PassFail"]

    def __init__(self, output_path: Path):
        super(LoadProfileExcelFormatter, self).__init__(
            output_path=output_path,
            test_specific_headers=self.TEST_SPECIFIC_HEADERS)

    def _testspecific_formatting(self, worksheet, column: int, first_row: int,
                                 last_row: int, value: str):
        if value in ["Power PassFail", "Current PassFail", "Min PassFail",
                     "Max PassFail"]:
            worksheet.conditional_format(first_row=first_row, first_col=column,
                                         last_row=last_row, last_col=column,
                                         options={'type': 'cell',
                                                  'criteria': 'equal',
                                                  'value': '"Pass"',
                                                  'format': self.pass_format})
            worksheet.conditional_format(first_row, column, last_row, column,
                                         {'type': 'cell',
                                          'criteria': 'equal',
                                          'value': '"Fail"',
                                          'format': self.fail_format})
            worksheet.conditional_format(first_row, column, last_row, column,
                                         {'type': 'cell',
                                          'criteria': 'equal',
                                          'value': '"N/A"',
                                          'format': self.na_format})
            worksheet.conditional_format(first_row, column, last_row, column,
                                         {'type': 'cell',
                                          'criteria': 'equal',
                                          'value': '"Reviewed"',
                                          'format': self.review_format})
