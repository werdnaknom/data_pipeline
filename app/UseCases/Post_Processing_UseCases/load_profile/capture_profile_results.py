from dataclasses import dataclass, field
from collections import OrderedDict
import typing as t

import numpy as np
import pandas as pd

from app.shared.Entities import *


@dataclass
class CaptureTestPoint():
    testpoint: str
    waveform_ids: pd.Series
    spec_max: float
    spec_min: float
    edge: bool
    wf_max: float = None
    wf_mean: float = None
    wf_min: float = None
    waveforms: t.List[WaveformEntity] = field(default_factory=list)
    HEADER_TESTPOINT: str = "testpoint"
    HEADER_SS_MIN: str = "SS Min (V)"
    HEADER_SS_MAX: str = "SS Max (V)"
    HEADER_SS_MEAN: str = "SS Mean (V)"
    HEADER_SPEC_MIN: str = "SS Spec Min (V)"
    HEADER_SPEC_MAX: str = "SS Spec Max (V)"
    HEADER_MAX_RESULT: str = "Max PassFail"
    HEADER_MAX_REASON: str = "Max Reason"
    HEADER_MIN_RESULT: str = "Min PassFail"
    HEADER_MIN_REASON: str = "Min Reason"

    def passfail(self):
        result = OrderedDict()
        wf_max, wf_mean, wf_min = self._waveform_analysis()

        result[self.HEADER_TESTPOINT] = self.testpoint
        result[self.HEADER_SS_MAX] = wf_max
        result[self.HEADER_SPEC_MAX] = self.spec_max
        result[self.HEADER_SPEC_MIN] = self.spec_min
        result[self.HEADER_SS_MIN] = wf_min
        result[self.HEADER_SS_MEAN] = wf_mean

        max_result, max_reason, min_result, min_reason = self._passfail(
            max=wf_max, min=wf_min)

        result[self.HEADER_MAX_RESULT] = max_result
        result[self.HEADER_MIN_RESULT] = min_result

        result[self.HEADER_MAX_REASON] = max_reason
        result[self.HEADER_MIN_REASON] = min_reason

        return result

    def _waveform_analysis(self) -> t.Tuple[float, float, float]:
        max_list = []
        mean_list = []
        min_list = []
        for wf in self.waveforms:
            if not self.edge:
                if wf.units == "A":
                    raise ValueError(f"{wf.testpoint} is not listed as an "
                                     f"edge rail but is a current "
                                     f"measurement. Is this a mistake? If on "
                                     f"purpose, contact me!")
                wf_y_ss = wf.y_axis()[wf.steady_state_index():]
            else:
                wf_y_ss = wf.y_axis()
            max = np.max(wf_y_ss)
            min = np.min(wf_y_ss)
            mean = np.mean(wf_y_ss)
            max_list.append(max)
            mean_list.append(mean)
            min_list.append(min)

        wf_max = np.max(max_list)
        wf_mean = np.mean(mean_list)
        wf_min = np.min(min_list)

        self.wf_mean = wf_mean
        self.wf_max = wf_max
        self.wf_min = wf_min

        return wf_max, wf_mean, wf_min

    def _passfail(self, max: float, min: float) -> t.Tuple[str, str, str, str]:
        if self.edge:
            max_result = "N/A"
            min_result = "N/A"
            max_reason = "Edge Rail"
            min_reason = "Edge Rail"
        else:
            if max <= self.spec_max:
                max_result = "Pass"
                max_reason = ""
            else:
                max_result = "Fail"
                max_reason = f"{round(max, 2)}>={self.spec_max}"

            if min >= self.spec_min:
                min_result = "Pass"
                min_reason = ""
            else:
                min_result = "Fail"
                min_reason = f"{round(min, 2)} <= {self.spec_min}"

        return max_result, max_reason, min_result, min_reason


@dataclass
class CaptureProfileResult():
    voltage_wfs: t.List[WaveformEntity]
    current_wfs: t.List[WaveformEntity]
    current_spec_max: float
    max_power: float
    power_wfs: t.List[np.array] = field(default_factory=list)
    HEADER_CURRENT_TESTPOINT: str = "Current Testpoint"
    HEADER_VOLTAGE_TESTPOINT: str = "Voltage Testpoint"
    HEADER_SPEC_CMAX: str = "Current Limit (A)"
    HEADER_CMAX: str = "Max Current(A)"
    HEADER_CMEAN: str = "Mean Current(A)"
    HEADER_SPEC_PMAX: str = "Power Limit (W)"
    HEADER_PMAX: str = "Max Power (W)"
    HEADER_PMEAN: str = "Mean Power (W)"
    HEADER_CRESULT: str = "Current PassFail"
    HEADER_CREASON: str = "Current Reason"
    HEADER_PRESULT: str = "Power PassFail"
    HEADER_PREASON: str = "Power Reason"

    def passfail(self) -> t.OrderedDict:
        result = OrderedDict()

        result[self.HEADER_CURRENT_TESTPOINT] = self.current_wfs[0].testpoint
        result[self.HEADER_VOLTAGE_TESTPOINT] = self.voltage_wfs[0].testpoint
        result[self.HEADER_SPEC_CMAX] = self.current_spec_max
        current_arrays = [wf.y_axis() for wf in self.current_wfs]
        result[self.HEADER_CMAX] = np.max(current_arrays)
        result[self.HEADER_CMEAN] = np.mean(current_arrays)
        result[self.HEADER_SPEC_PMAX] = self.max_power
        result[self.HEADER_PMAX] = np.max(self.power_waveforms())
        result[self.HEADER_PMEAN] = np.mean(self.power_waveforms())

        power_result, power_reason = self._power_passfail()
        result[self.HEADER_PRESULT] = power_result
        result[self.HEADER_PREASON] = power_reason

        current_result, current_reason = self._current_passfail(
            current_arrays=current_arrays)
        result[self.HEADER_CRESULT] = current_result
        result[self.HEADER_CREASON] = current_reason

        return result

    def _current_passfail(self, current_arrays):
        max_current = np.max(current_arrays)
        if max_current == np.NaN:
            current_result = "N/A"
            reason = "No Current Waveform"
        elif max_current <= self.current_spec_max:
            current_result = "Pass"
            reason = f"{max_current}A <= {self.current_spec_max}A"
        else:
            current_result = "Fail"
            reason = f"{max_current}A > spec {self.current_spec_max}A"
        return current_result, reason
