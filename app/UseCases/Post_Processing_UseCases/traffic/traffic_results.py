from dataclasses import dataclass, field
from collections import OrderedDict
import typing as t

import numpy as np
import pandas as pd

from app.shared.Entities import *

from app.shared.Entities.file_entities import Port


@dataclass
class PortResult:
    dut: Port
    lp: Port
    RESULT = ""
    REASON = ""

    def passfail(self) -> OrderedDict:
        raise NotImplementedError

    def to_result(self) -> OrderedDict:
        return OrderedDict([
            ("Port", self.dut.port)
        ])


@dataclass
class PortErrorResult(PortResult):
    RESULT = "Traffic Result"
    REASON = "Traffic Reason"

    def passfail(self) -> OrderedDict:
        result = OrderedDict([
            (self.RESULT, "Invalid"),
            (self.REASON, "PostProcessing Ran Incorrectly...?")
        ])

        try:
            if not self.dut.port == self.lp.port:
                result[
                    self.REASON] = "Setup Error: DUT and LP ports not equal! " \
                                   f"{self.dut.port} != {self.lp.port}"
                result[self.RESULT] = "Fail"
                return result
            elif self.dut.rx_errors == 0 & self.dut.tx_errors == 0 & \
                    self.lp.rx_errors == 0 & self.lp.tx_errors == 0:
                result[self.REASON] = "No Errors"
                result[self.RESULT] = "Pass"
                return result
            elif self.dut.rx_errors >= 1 or self.dut.tx_errors >= 1:
                result[self.REASON] = "Errors detected on DUT:\n" \
                                      f"Rx: {self.dut.rx_errors}\n " \
                                      f"Tx: {self.dut.tx_errors}"

                result[self.RESULT] = "Fail"
                return result
            elif self.lp.rx_errors >= 1 or self.lp.tx_errors >= 1:
                result[self.REASON] = "Errors detected on LP:\n" \
                                      f"Rx: {self.lp.rx_errors}\n " \
                                      f"Tx: {self.lp.tx_errors}"
                result[self.RESULT] = "Warning"
                return result
            else:
                return result
        except TypeError as e:
            result[self.REASON] = e
            result[self.RESULT] = "Invalid. ATS2 failure."
            return result

    def to_result(self) -> OrderedDict:
        result = super(PortErrorResult, self).to_result()
        result.update(self.passfail())
        return result


@dataclass
class PortConfidenceLevelResult(PortResult):
    RESULT = "Confidence Level Result"
    REASON = "Confidence Level Reason"
    confidence_level: int
    specified_ber: float

    # This function computes the confidence level based on the bits received and BER
    @classmethod
    def confidence_level_calc(cls, bits: int, errors: int,
                              specified_BER: float) -> float:
        # if there are errors, the BER test fails
        if errors != 0:
            cl = 0
            return cl
        cl = (1 - (1 - specified_BER) ** bits) * 100
        return round(cl, 2)

    def passfail(self) -> OrderedDict:
        bits = self.dut.bits_recv(lp_pkt_size=self.lp.packet_size)
        errors = self.dut.rx_errors
        conf_level_calc = self.confidence_level_calc(bits=bits, errors=errors,
                                                     specified_BER=self.specified_ber)

        results = OrderedDict([
            (self.RESULT, "Invalid"),
            (self.REASON, "PostProcessing Ran Incorrectly...?"),
            ("Target BER", self.specified_ber),
            ("DUT Bits Recv", bits),
            ("Calc. CL", conf_level_calc)
        ])
        if self.confidence_level <= conf_level_calc:
            results[
                self.REASON] = f"{self.confidence_level} <= {conf_level_calc}"
            results[self.RESULT] = "Pass"
        else:
            results[self.REASON] = "Not Enough bits sent: " \
                                   f"{self.confidence_level} > {conf_level_calc}"
            results[self.RESULT] = "Fail"

        return results

    def to_result(self) -> OrderedDict:
        result = super(PortConfidenceLevelResult, self).to_result()
        result.update(self.passfail())
        return result


@dataclass
class BERGroupResult():
    df: pd.DataFrame = pd.DataFrame()
    errors: t.List[PortErrorResult] = field(default_factory=list)
    confidence_levels: t.List[PortConfidenceLevelResult] = field(
        default_factory=list)

    def add_result(self, row_dict: OrderedDict, error_result: PortErrorResult,
                   confidence_result: PortConfidenceLevelResult):
        row_dict.update(error_result.to_result())
        row_dict.update(confidence_result.to_result())

        if self.df.empty:
            self.df = pd.DataFrame(row_dict, columns=list(row_dict.keys()),
                                   index=[0])
        else:
            self.df = self.df.append(row_dict, ignore_index=True)


'''
@dataclass
class TrafficGroupResult():
    df: pd.DataFrame
    capture_number: int
    results: t.List[TrafficPortResult] = field(default_factory=list)
    GROUP_RESULT = "Group Result"
    RESULT = "Result"

    def add_result(self, result: TrafficPortResult):
        self.results.append(result)

    def to_result(self) -> pd.DataFrame:
        indiv_results = [r.to_result() for r in self.results]
        result_df = pd.DataFrame(indiv_results,
                                 columns=list(indiv_results[0].keys()))
        group_results = result_df[self.RESULT].unique()
        if len(group_results) == 1:
            result_df[self.GROUP_RESULT] = group_results[0]
        elif "Invalid" in group_results:
            result_df[self.GROUP_RESULT] = "Invalid"
        else:
            result_df[self.GROUP_RESULT] = "Fail"

        return result_df
'''
