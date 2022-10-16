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
from app.UseCases.Post_Processing_UseCases.waveform_poweron_timing \
    .waveform_poweron_timing_usecase import PowerOnTimingRequestObject, \
    PowerOnTimingUseCase

from app.UseCases.Post_Processing_UseCases.capture_timing \
    .capture_timing_use_case import CaptureTimingRequestObject, \
    CaptureTimingUseCase

from app.shared.Entities import Entity

# from app.UseCases.Post_Processing_UseCases.waveform_timing\
#    .waveform_timing_use_case import WaveformTimingUseCase

from app.UseCases.Post_Processing_UseCases.waveform_sequencing \
    .waveform_sequencing2_use_case import WaveformSequencingUseCase, \
    WaveformSequencingRequestObject

from app.shared.ExcelWriter.excel_formats import FormattingExcelDataFrame

TIMING_COL = "timing_ms"


class SequencingUseCase(AutomationTestUseCase):
    _name = "Sequencing"
    LAST_FILTERBY: str = "testpoint"

    def process_request(self,
                        request_object: AutomationTestRequestObject) -> Response:
        """
        Sequencing Automation Test Case takes the combined dataframe from the
        input functions and filters it by filter_by and the LAST_FILTERBY to
        create a groups of captures.


        The sequencing test has to do 3 main functions for each capture:
            - Validate waveform_names ramp in the correct order
            - Validate the timing between waveform_names
            - Validate all waveform_names are up within a certain time
            - Validate Waveforms

        @param request_object:
        @return:
        """

        """
            The sequencing automation test takes the combined dataframe from 
            the input functions and filters it by filter_by and the 
            LAST_FILTERBY to create a group_df of individual captures.  

            Sequencing needs to be analyzed on a capture basis because 
            the timings from CH1 turning on to all the other rails needs to 
            be found.

            Once the timings have been found, the test can analyze based on 
            the filter_by metric the user selected.
        """

        timed_df = self.calculate_capture_timings(df=request_object.df)

        sequencing_result_df = pd.DataFrame()
        poweron_result_df = pd.DataFrame()
        groupby_list = self.set_filter_by_list(
            filter_by=request_object.filter_by, what_default="capture")

        # Last Filterby is testpoint. This removes that for the entity dict.
        groupby_list_without_testpoint = groupby_list[:-1]

        entity_dict = OrderedDict()
        feature_dict = OrderedDict()

        for filters, group_df in timed_df.groupby(
                by=groupby_list_without_testpoint):
            # Remove testpoint filter
            # filters = filters[:-1]
            entity_dict = self.process_filter_entities(filter_tuple=filters,
                                                       groupby_list=groupby_list_without_testpoint,
                                                       entity_dict=entity_dict)

            actual_filters = tuple(entity.descriptor for entity in
                                   entity_dict.values())

            sequencing_df, poweron_timing_df = self.execute_use_cases(
                df=group_df,
                filter_tuple=actual_filters,
                entity_dict=entity_dict)
            sequencing_result_df = pd.concat(
                [sequencing_result_df, sequencing_df])

            poweron_result_df = pd.concat(
                [poweron_result_df, poweron_timing_df])

        # Write DF to excel File
        data_dict = OrderedDict([
            ("Sequencing", sequencing_result_df),
            ("Power-On Time", poweron_result_df)
        ])

        excel_path_str = self.build_excel_file(data_dict=data_dict)

        return ResponseSuccess(value=excel_path_str)

    def execute_use_cases(self, df: pd.DataFrame, filter_tuple: t.Tuple[
        t.Any], entity_dict: t.OrderedDict[str, Entity]) -> \
            t.OrderedDict[str, pd.DataFrame]:
        '''
        Executes the Sequencing UseCases
            1) Power-on Time
            2) Voltage Rail Sequencing
        @param df:
        @param filter_by:
        @return:
        '''

        # sequencing_test_filterby = self.set_filter_by_list(filter_by=filter_by,
        #                                                   what_default='capture')

        feature_dict = OrderedDict()

        # 1) Waveform Sequencing
        sequencing_req = WaveformSequencingRequestObject(df=df,
                                                         filter_tuple=filter_tuple)
        uc = WaveformSequencingUseCase(repo=self.repo)
        seq_resp = uc.execute(request_object=sequencing_req)

        seq_df = self.combine_filters_with_results(entity_dict=entity_dict,
                                                   feature_dict=feature_dict,
                                                   response=seq_resp)

        # 2) Timing Between Waveforms
        # uc = WaveformTimingUseCase(repo=self.repo)
        # timing_resp = uc.execute(request_object=pp_req)

        # 3) Power-on Time
        powerOn_req = PowerOnTimingRequestObject(df=df,
                                                 filter_tuple=filter_tuple)

        uc = PowerOnTimingUseCase(repo=self.repo)
        power_on_timing_resp = uc.execute(request_object=powerOn_req)

        poweron_df = self.combine_filters_with_results(entity_dict=entity_dict,
                                                       feature_dict=feature_dict,
                                                       response=power_on_timing_resp)

        # 4) Validate Waveforms
        # uc = ValidateWaveformUseCase(repo=self.repo)
        # waveform_names = uc.execute(request_object=pp_req)

        return seq_df, poweron_df

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
        xlsx_formatter = SequencingExcelFormatter(output_path=output_path)

        for sheet_name, df in data_dict.items():
            xlsx_formatter.write_sheet(sheetname=sheet_name, df=df)

        xlsx_formatter.save_excel()

        return output_path


class SequencingExcelFormatter(FormattingExcelDataFrame):
    TEST_SPECIFIC_HEADERS = ["Sequencing Result", "Timing Result"]

    def __init__(self, output_path: Path):
        super(SequencingExcelFormatter, self).__init__(
            output_path=output_path,
            test_specific_headers=self.TEST_SPECIFIC_HEADERS)

    def _testspecific_formatting(self, worksheet, column: int,
                                 first_row: int,
                                 last_row: int, value: str):
        if value in ["Sequencing Result", "Timing Result"]:
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
