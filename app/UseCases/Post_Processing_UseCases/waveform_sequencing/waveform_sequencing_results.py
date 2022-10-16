from dataclasses import dataclass, field
from collections import OrderedDict
import typing as t

import numpy as np
import pandas as pd

from app.shared.Entities import *


@dataclass
class SequencingHeaders():
    HEADER_TESTPOINT: str = "testpoint"
    HEADER_EXP_ORDER: str = "expected order"
    HEADER_MIN: str = "min time (ms)"
    HEADER_MAX: str = "max time (ms)"
    HEADER_SPEC_MIN: str = "min spec (ms)"
    HEADER_SPEC_MAX: str = "max spec (ms)"
    HEADER_WF_ID: str = "waveform_id"


@dataclass
class SequencingResult():
    order: int
    t0: float
    min_time: float
    max_time: float
    spec_min: float
    spec_max: float


@dataclass
class TestpointTimingResult(SequencingResult):
    '''
    Individual testpoint results validate that the rail ramped within the
    specified time.  The userinput file defines the maximum ramp time from
    t0, which the test calculates as the time that the edge rail meets it's
    steady state voltage.
    '''
    testpoint: str
    waveform_id: str
    HEADER_TESTPOINT: str = "testpoint"
    HEADER_EXP_ORDER: str = "Expected Order"
    HEADER_MIN: str = "Min Time (ms)"
    HEADER_MAX: str = "Max Time (ms)"
    HEADER_SPEC_MIN: str = "Min Spec (ms)"
    HEADER_SPEC_MAX: str = "Max Spec (ms)"
    HEADER_WF_ID: str = "waveform_id"
    HEADER_GROUPNUM: int = "Group"

    def __post_init__(self):
        self.RESULT: str = "Timing"
        self.REASON: str = "Timing Reason"

    def average_time(self):
        return np.average([self.min_time, self.max_time])

    def t0_min(self) -> float:
        result = self.min_time - self.t0
        return result

    def t0_max(self) -> float:
        result = self.max_time - self.t0
        return result

    def pass_min_time(self) -> bool:
        if self.t0_min() >= self.spec_min:
            return True
        else:
            return False

    def pass_max_time(self) -> bool:
        if self.t0_max() <= self.spec_max:
            return True
        else:
            return False

    def passfail(self) -> OrderedDict:
        result = OrderedDict()
        if self.pass_max_time() and self.pass_min_time():
            result[self.RESULT] = "Pass"
            result[self.REASON] = ""
        elif self.pass_max_time() and not self.pass_min_time():
            result[self.RESULT] = "Fail"
            result[self.REASON] = \
                f"Min Time [{self.t0_min()}] < Spec Min [{self.spec_min}]"
        elif not self.pass_max_time() and self.pass_min_time():
            result[self.RESULT] = "Fail"
            result[self.REASON] = \
                f"Max Time [{self.t0_max()}] > Spec Max [{self.spec_max}]"
        else:
            result[self.RESULT] = "Fail"
            result[self.REASON] = \
                f"Min Time [{self.t0_min()}] < Spec Min [{self.spec_min}] and " \
                f"Max Time [{self.t0_max()}] > Spec Max [{self.spec_max}]"
        return result

    def to_result(self) -> OrderedDict:
        result_dict = OrderedDict([
            (self.HEADER_TESTPOINT, self.testpoint),
            (self.HEADER_EXP_ORDER, self.order),
            (self.HEADER_MIN, self.min_time - self.t0),
            (self.HEADER_SPEC_MIN, self.spec_min),
            (self.HEADER_MAX, self.max_time - self.t0),
            (self.HEADER_SPEC_MAX, self.spec_max),
            (self.HEADER_WF_ID, self.waveform_id)
        ])
        result_dict.update(self.passfail())
        return result_dict


@dataclass
class SequencingCaptureResult():
    '''
    The capture group validates the trace order is correct.  Each waveform
    within the group is validated to come up in the correct order based on
    their ramp timing.

    input: list of TestpointTimingResult from a single capture
    output: dataframe and/or single capture result
    '''
    capture_number: int
    results: t.List[TestpointTimingResult] = field(default_factory=list)
    allowed_variance:t.List[float] = field(default_factory=list)
    HEADER_TESTPOINT: str = "testpoint"
    HEADER_EXP_ORDER: str = "Expected Order"
    HEADER_MIN: str = "Min Time (ms)"
    HEADER_MAX: str = "Max Time (ms)"
    HEADER_SPEC_MIN: str = "Min Spec (ms)"
    HEADER_SPEC_MAX: str = "Max Spec (ms)"
    HEADER_WF_ID: str = "waveform_id"
    HEADER_GROUPNUM: int = "Group"

    def __post_init__(self):
        self.GROUP_RESULT = "Group Result"
        self.RESULT: str = "Order"
        self.REASON: str = "Order Reason"

    def add_result(self, result: TestpointTimingResult):
        self.results.append(result)

    def passfail(self):
        result = OrderedDict([
            (self.RESULT, "Invalid"),
            (self.REASON, "Something went wrong...?")
        ])

        ordered_df = self._create_df()

        monotonic = ordered_df[self.HEADER_MIN].is_monotonic_increasing

        if monotonic:
            result[self.RESULT] =  "Pass"
            result[self.REASON] = "minimum time is monotonic"
        else:
            result[self.RESULT] = "Fail"
            order_by_time_df = ordered_df.sort_values(by=self.HEADER_MIN)
            result[self.REASON] = "->".join(str(o) for o in
                                            order_by_time_df[
                                                self.HEADER_EXP_ORDER])

        return result


    def _create_df(self) -> pd.DataFrame:
        indiv_results = [r.to_result() for r in self.results]
        df = pd.DataFrame(indiv_results,
                               columns=list(indiv_results[0].keys()))

        ordered_df = df.sort_values(by=self.HEADER_EXP_ORDER)
        return ordered_df

    def to_result(self) -> OrderedDict:
        result = self.passfail()




@dataclass
class SequencingGroupResult(SequencingResult):
    pass
