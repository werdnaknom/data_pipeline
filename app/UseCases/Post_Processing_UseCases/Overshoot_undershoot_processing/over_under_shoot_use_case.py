import typing as t
import itertools
from collections import defaultdict

import pandas as pd

from pandas import ExcelWriter

import gc
import sys
from pathlib import Path
# from shutil import rmtree
# from zipfile import ZipFile


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.UseCases.Post_Processing_UseCases.post_processing_use_case import \
    PostProcessingUseCase, PostProcessingRequestObject
from app.shared.Entities import WaveformEntity

plt.style.use("ggplot")
WAVEFORM_DICT = t.NewType("WAVEFORM_DICT", t.Dict[str, t.List[WaveformEntity]])


class OverUnderShootProcessingUseCase(PostProcessingUseCase):
    sheet_name = "Waveform Over-Undershoot"
    EDGE_RAIL_COLUMN_HEADER = "edge_rail"

    # TRACE_ORDER_COLUMN_HEADER = "trace_order"
    # POWER_ON_TIME_COLUMN_HEADER = "power_on_time_spec"
    # TIME_DELTA_COLUMN_HEADER = "time_delta"

    def _test_specific_columns(self):
        '''

        @return:
        return [self.EDGE_RAIL_COLUMN_HEADER, self.TRACE_ORDER_COLUMN_HEADER,
                self.POWER_ON_TIME_COLUMN_HEADER, self.TIME_DELTA_COLUMN_HEADER]
        '''
        return [self.EDGE_RAIL_COLUMN_HEADER]

    def post_process(self, request_object: PostProcessingRequestObject) -> \
            pd.DataFrame:
        """
        The Sequencing Test validates the waveform_names ramp in the correct order
        and within the given time limit.
            - Validate waveform sequence
            - Validate waveform ramp timing

        @param request_object:
        @return:
        """
        # Filter raw dataframe

        filtered_df = self.filter_df(raw_df=request_object.df)

        by = request_object.groupby_list
        if not len(by):
            by = ["dut", "pba", "rework", "serial_number", "runid", "capture"]

        return pd.DataFrame({"A": [1, 2, 4, 5, 6]})
