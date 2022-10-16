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


class TestpointTimingResult2():
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


@dataclass
class TraceOrderGroup():
    order: int
    df: pd.DataFrame

    def max_timing(self, df=None) -> float:
        if not isinstance(df, pd.DataFrame):
            df = self.df
        return df["t0_to_poweron"].max()

    def min_timing(self, df=None) -> float:
        if not isinstance(df, pd.DataFrame):
            df = self.df
        return df["t0_to_poweron"].min()

    def mean_timing(self, df=None) -> float:
        if not isinstance(df, pd.DataFrame):
            df = self.df
        return df["t0_to_poweron"].mean()

    def testpoints(self) -> list:
        return list(self.df["testpoint"].unique())

    def human_display(self, odict: OrderedDict, result_type="mean"):
        COLUMN_FMT = "{result_type} Timing: {testpoint} ({order})"
        ordered_df = self.df.sort_values(by=["trace_order"])
        for filter, df in ordered_df.groupby(by=["trace_order", "testpoint"]):
            if result_type == "mean":
                result_value = self.mean_timing(df=df)
            elif result_type == "max":
                result_value = self.max_timing(df=df)
            elif result_type == "min":
                result_value = self.min_timing(df=df)
            else:
                raise TypeError(f"result_type={result_type} is invalid for "
                                f"TraceOrderGrouping!")

            trace_order, testpoint = filter
            col = COLUMN_FMT.format(testpoint=testpoint, order=int(trace_order),
                                    result_type=result_type.title())
            odict[col] = result_value

        return odict


class SequencingResult():
    test_name: str = "Sequencing"
    tOrderGroups: t.List[TraceOrderGroup] = field(default_factory=list)

    RESULT: str = "Sequencing Result"
    REASON: str = "Sequencing Reason"

    def __init__(self, df: pd.DataFrame):
        # self.timing_results = sorted(timing_results, key=lambda obj:
        # obj.spec_trace_order)
        self.df = self._cleanup_dataframe(df=df)
        self.tOrderGroups = self._reorder_testpoints_by_expected_order()

    def _cleanup_dataframe(self, df: pd.DataFrame):
        new_df = df[["runid", "capture", "testpoint", "trace_order",
                     "power_on_time_spec", "poweron_index", "capture_t0",
                     "t0_to_poweron", "total_poweron_time"]]
        new_df.sort_values(by=["power_on_time_spec"], inplace=True)
        return new_df

    def _reorder_testpoints_by_expected_order(self):
        group_list = []
        for i, (filters, df) in enumerate(self.df.groupby(by=[
            "power_on_time_spec"])):
            tOrderGroup = TraceOrderGroup(order=i, df=df)
            group_list.append(tOrderGroup)

        return group_list

    # def __get_df_

    def sequencing_fail_metric(self) -> t.Tuple[str, str]:
        '''

        @return:  PASS/FAIL VALUE, PASS/FAIL REASON
        '''
        n = self.tOrderGroups[0]
        for nPlus1 in self.tOrderGroups[1:]:

            # N + 1 minimum timing should always be longer than N maximum timing
            n1_minimum = nPlus1.df["t0_to_poweron"].min()
            n_maximum = n.df["t0_to_poweron"].max()

            if n1_minimum <= n_maximum:
                return "Fail", f"{nPlus1.testpoints()}{n1_minimum} < " \
                               f"{n.testpoints()}{n_maximum}"
        return "Pass", ""

    def passfail(self):
        result_dict = OrderedDict()

        result, result_reason = self.sequencing_fail_metric()

        for trace_group in self.tOrderGroups:
            result_dict = trace_group.human_display(odict=result_dict,
                                                    result_type="mean")
        result_dict[self.RESULT] = result
        result_dict[self.REASON] = result_reason

        return result_dict

    """

    def _determine_passfail(self):
        order = self.timing_results
        min_timings
        mean_timings
        max_timings

    def passfail(self) -> OrderedDict:
        result = OrderedDict()
        for order in
            return result
    """
