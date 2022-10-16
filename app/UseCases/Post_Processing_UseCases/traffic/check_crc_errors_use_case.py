import typing as t
import itertools
from collections import defaultdict, OrderedDict

import pandas as pd

from pandas import ExcelWriter

import gc
import sys
from pathlib import Path
import numpy as np

from app.UseCases.Post_Processing_UseCases.post_processing_use_case import \
    PostProcessingUseCase, PostProcessingRequestObject
from app.shared.Entities.entities import EthAgentCaptureEntity
from app.UseCases.Post_Processing_UseCases.traffic.traffic_results import \
    BERGroupResult, PortConfidenceLevelResult, PortErrorResult, PortResult


class TrafficProcessingUseCase(PostProcessingUseCase):
    sheet_name = "BitErrorRatio"
    CONFIDENCE_LEVEL_COLUMN_HEADER = "confidence_level"
    TARGET_BER_COLUMN_HEADER = "target_ber"
    waveform_test = False

    def _test_specific_columns(self):
        return [self.CONFIDENCE_LEVEL_COLUMN_HEADER,
                self.TARGET_BER_COLUMN_HEADER]

    def post_process(self, request_object: PostProcessingRequestObject) -> \
            pd.DataFrame:
        results_df = self.make_results_df2(filtered_df=request_object.df,
                                           merge_columns=[])

        return results_df

    def format_row(self, result_row: OrderedDict):
        pass

    def business_logic(self, result_row: OrderedDict, confidence_level: int,
                       specified_ber: float,
                       ethagent_capture: EthAgentCaptureEntity) -> pd.DataFrame:
        """
        Test specific Pass/Fail criteria goes here

        @param kwargs:
        @return:
        """
        dut = ethagent_capture.dut
        lp = ethagent_capture.lp

        group_result = BERGroupResult()
        for dut_port, lp_port in zip(dut.ports, lp.ports):
            result_row.update(dut_port.to_result(suffix=dut.device_fmt))
            result_row.update(lp_port.to_result(suffix=lp.device_fmt))
            error_result = PortErrorResult(dut=dut_port, lp=lp_port)
            confidence_result = PortConfidenceLevelResult(dut=dut_port,
                                                          lp=lp_port,
                                                          confidence_level=confidence_level,
                                                          specified_ber=specified_ber)

            group_result.add_result(row_dict=result_row,
                                    error_result=error_result,
                                    confidence_result=confidence_result)

        if len(dut.ports) != len(lp.ports):
            pass

        return group_result.df
