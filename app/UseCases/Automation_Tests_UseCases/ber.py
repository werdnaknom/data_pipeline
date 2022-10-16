from __future__ import annotations
import typing as t

import pandas as pd
from collections import OrderedDict
from pathlib import Path

from app.UseCases.Automation_Tests_UseCases.automation_test_usecase import \
    AutomationTestUseCase, AutomationTestRequestObject
from app.shared.Responses.response import Response, ResponseSuccess

from app.UseCases.Post_Processing_UseCases.traffic.check_crc_errors_use_case \
    import TrafficProcessingUseCase, PostProcessingRequestObject

from app.shared.ExcelWriter.excel_formats import FormattingExcelDataFrame


class BitErrorRatioUseCase(AutomationTestUseCase):
    _name = "BER"
    LAST_FILTERBY: str = "testpoint"

    def process_request(self,
                        request_object: AutomationTestRequestObject) -> Response:
        """
        The Bit Error Ratio test has to do 3 main functions for each capture:
            - Validate there were no rx bit errors (DUT and LP)
            - Validate there were no tx bit errors (DUT and LP)
            - Validate an appropriate number of bits were sent to meet the
            confidence level

        @param request_object: The request object has two features:
            df: pd.DataFrame
            filter_by: t.List[str] = ["dut", "pba", "rework", "serial_number", "runid",
                              "capture"]
        @return: Response Success with value equal to path of excel output file
        """

        # 1) Validate there were no rx bit errors
        # 2) Validate there were no tx bit errors
        # 3) Validate an appropriate number for bits were sent to meet the
        # requirements
        pp_req = PostProcessingRequestObject(filters=request_object.filter_by,
                                             df=request_object.df)

        uc = TrafficProcessingUseCase(repo=self.repo)
        resp = uc.execute(request_object=pp_req)
        sheet_name, df = resp.value
        result_dict = OrderedDict([
            (sheet_name, df)
        ])

        excel_path = self.build_excel_file(data_dict=result_dict)

        return ResponseSuccess(value=excel_path)

    def _build_excel_file(self, output_path: Path,
                          data_dict: t.OrderedDict[str, pd.DataFrame]) -> str:
        """

        @param output_path:  Path
        @return: path to excel writer

        """
        xlsx_formatter = BERExcelFormatter(output_path=output_path)

        for sheet_name, df in data_dict.items():
            xlsx_formatter.write_sheet(sheetname=sheet_name, df=df)

        xlsx_formatter.save_excel()

        return output_path


class BERExcelFormatter(FormattingExcelDataFrame):
    TEST_SPECIFIC_HEADERS = ["Traffic Result", "Confidence Level Result"]

    def __init__(self, output_path: Path):
        super(BERExcelFormatter, self).__init__(output_path=output_path,
                                                test_specific_headers=self.TEST_SPECIFIC_HEADERS)

    def _testspecific_formatting(self, worksheet, column: int, first_row: int,
                                 last_row: int, value: str):
        if "Result" in value:
            self.conditional_format_passfail(worksheet=worksheet,
                                             column=column,
                                             last_row=last_row,
                                             first_row=first_row)
