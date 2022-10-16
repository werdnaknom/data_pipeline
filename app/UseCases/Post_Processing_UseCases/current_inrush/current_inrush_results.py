from dataclasses import dataclass, field
from collections import OrderedDict
import typing as t

import numpy as np
import pandas as pd

from app.shared.Entities import *


@dataclass
class CaptureInrushResult():
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

    def power_waveforms(self):
        if self.power_wfs:
            return self.power_wfs
        else:
            for current_wf, voltage_wf in zip(self.current_wfs,
                                              self.voltage_wfs):
                current_array = np.array(current_wf.y_axis())
                voltage_array = np.array(voltage_wf.y_axis())
                power_array = current_array * voltage_array
                self.power_wfs.append(power_array)
            return self.power_wfs

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

    def _power_passfail(self) -> t.Tuple[str, str]:

        max_power = np.max(self.power_waveforms())
        if max_power == np.NaN:
            power_result = "N/A"
            reason = "No Voltage Waveform"
        elif max_power <= self.max_power:
            power_result = "Pass"
            reason = f"{max_power}W <= {self.max_power}W"
        else:
            power_result = "Fail"
            reason = f"{max_power}W > spec {self.max_power}W"
        return power_result, reason

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
