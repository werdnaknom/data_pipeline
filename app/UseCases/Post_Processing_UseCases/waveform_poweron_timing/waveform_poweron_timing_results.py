from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
import typing as t

import numpy as np
import pandas as pd

from app.shared.Entities import *

DF_WAVEFORM_ID: str = "waveform_id"
DF_TESTPOINT: str = "testpoint"
DF_CAPTURE_T0_INDEX: str = "capture_t0_index"
DF_T0_TO_POWERON: str = "t0_to_poweron"
DF_TOTAL_POWERON_TIME: str = "total_poweron_time"
DF_POWERON_INDEX: str = "poweron_index"
DF_VALID_VOLTAGE: str = "valid_voltage"
DF_TRACE_ORDER: str = "trace_order"
DF_POWER_ON_TIME_SPEC: str = "power_on_time_spec"
DF_TIME_DELTA: str = "time_delta"


class TestpointTimingResult():
    test_name: str = "Timing"

    testpoint: str = ""
    mean_timing: float = None
    max_timing: float = None
    min_timing: float = None
    mode_timing: float = None
    spec_timing_max: float = None
    spec_trace_order: float = None

    RESULT: str = "Timing Result"
    REASON: str = "Timing Reason"
    _debug = False

    def __init__(self, df: pd.DataFrame):
        df = df[[DF_WAVEFORM_ID, DF_TESTPOINT,
                 DF_CAPTURE_T0_INDEX, DF_T0_TO_POWERON,
                 DF_TOTAL_POWERON_TIME, DF_POWERON_INDEX,
                 DF_VALID_VOLTAGE, DF_TRACE_ORDER,
                 DF_POWER_ON_TIME_SPEC, DF_TIME_DELTA]]
        self._extract_testpoint(df=df)
        self._extract_specs(df=df)
        self.poweron_timings(df=df)

    def _extract_testpoint(self, df: pd.DataFrame) -> None:
        testpoint_array = df[DF_TESTPOINT].unique()

        assert len(testpoint_array == 1), \
            "More than one testpoint was in the TestpointTimingResult " \
            "dataframe."
        self.testpoint = testpoint_array[0]

    def _extract_specs(self, df: pd.DataFrame) -> None:
        spec_timing_max = df[DF_POWER_ON_TIME_SPEC].unique()
        spec_trace_order = df[DF_TRACE_ORDER].unique()

        assert len(spec_timing_max) == 1, "In TimingResult the spec timing " \
                                          "had multiple unique values." \
                                          f" {spec_timing_max}"
        assert len(spec_trace_order) == 1, "In TimingResult the spec" \
                                           " trace order had multiple " \
                                           "unique values." \
                                           f" {spec_trace_order}"

        self.spec_timing_max = spec_timing_max[0]
        self.spec_trace_order = spec_trace_order[0]

    def get_spec_timing(self):
        return self.spec_timing_max

    def get_spec_trace_order(self):
        return self.spec_trace_order

    def poweron_timings(self, df: pd.DataFrame) -> None:
        timings = df[DF_T0_TO_POWERON].agg(["max", "min", "mean"])
        self.max_timing = timings['max']
        self.min_timing = timings['min']
        self.mean_timing = timings['mean']

        self.mode_timing = self._mode_poweron_timing(
            data_series=df[DF_T0_TO_POWERON])

    def _mode_poweron_timing(self, data_series: pd.Series) -> float:
        '''
        Calculates the mode of the data_series
        @return: float
        '''
        round_series = data_series.round(decimals=1)
        mode = round_series.value_counts().idxmax()
        bins = data_series.value_counts(bins=10)

        return mode

    def passfail(self) -> OrderedDict:
        result = OrderedDict()
        result['Min Timing (ms)'] = self.min_timing
        result['Mean Timing (ms)'] = self.mean_timing
        result["Max Timing (ms)"] = self.max_timing
        if self.spec_timing_max >= self.max_timing:
            result[self.RESULT] = "Pass"
            result[self.REASON] = f"Spec Max ({self.spec_timing_max}) >= " \
                                  f"{round(self.max_timing, 2)}"
        else:
            result[self.RESULT] = "Fail"
            result[self.REASON] = f"Spec Max ({self.spec_timing_max}) < " \
                                  f"{round(self.max_timing, 2)}"

        return result
