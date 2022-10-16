from dataclasses import dataclass, field
from collections import OrderedDict
import typing as t

import numpy as np
import pandas as pd

from app.shared.Entities import *


@dataclass
class TestPointMinMaxResult():
    HEADER_TESTPOINT: str = "Testpoint"
    HEADER_SS_MIN: str = "SS Min (V)"
    HEADER_SS_MAX: str = "SS Max (V)"
    HEADER_SS_MEAN: str = "SS Mean (V)"
    HEADER_SS_PK2PK: str = "SS Pk2Pk (V)"
    HEADER_MIN: str = "Min (V)"
    HEADER_MAX: str = "Max (V)"
    HEADER_SPEC_MIN: str = "SS Spec Min (V)"
    HEADER_SPEC_MAX: str = "SS Spec Max (V)"
    HEADER_WF_ID: str = "waveform_id"
    HEADER_RESULT: str = "PassFail"
    HEADER_REASON: str = "REASON"

    def passfail(self, entity: WaveformEntity, spec_min: float, spec_max: float) \
            -> OrderedDict:
        result = OrderedDict()
        result[self.HEADER_TESTPOINT] = entity.testpoint
        result[self.HEADER_MAX] = entity.max
        result[self.HEADER_MIN] = entity.min
        result[self.HEADER_SPEC_MAX] = spec_max
        result[self.HEADER_SS_MAX] = entity.steady_state_max
        result[self.HEADER_SPEC_MIN] = spec_min
        result[self.HEADER_SS_MIN] = entity.steady_state_min
        result[self.HEADER_SS_MEAN] = entity.steady_state_mean
        result[self.HEADER_SS_PK2PK] = entity.steady_state_pk2pk

        if entity.edge:
            passfail = "N/A"
            reason = "Edge rail"
        elif (entity.steady_state_max <= spec_max) and \
                (entity.steady_state_min >= spec_min):
            passfail = "Pass"
            reason = "Within Limits"
        else:
            passfail = "Fail"
            reason = ""
            if entity.steady_state_max > spec_max:
                reason += "SS Max > Spec Max"
            if entity.steady_state_min < spec_min:
                if reason:
                    reason += "\n"
                reason += "SS Min < Spec Min"

        result[self.HEADER_RESULT] = passfail
        result[self.HEADER_REASON] = reason

        return result

    def flatten(self, df: pd.DataFrame) -> pd.DataFrame:
        result_dict = OrderedDict()
        result_dict[self.HEADER_TESTPOINT] = df[self.HEADER_TESTPOINT].iloc[0]
        result_dict[self.HEADER_MAX] = np.max(df[self.HEADER_MAX])
        result_dict[self.HEADER_MIN] = np.min(df[self.HEADER_MIN])
        result_dict[self.HEADER_SPEC_MAX] = np.min(df[self.HEADER_SPEC_MAX])
        result_dict[self.HEADER_SS_MAX] = np.max(df[self.HEADER_SS_MAX])
        result_dict[self.HEADER_SPEC_MIN] = np.max(df[self.HEADER_SPEC_MIN])
        result_dict[self.HEADER_SS_MIN] = np.min(df[self.HEADER_SS_MIN])
        result_dict[self.HEADER_SS_MEAN] = np.mean(df[self.HEADER_SS_MEAN])
        result_dict[self.HEADER_SS_PK2PK] = np.max(df[self.HEADER_SS_PK2PK])
        passfail, reason = self._flatten_passfail(passfail=df[
            self.HEADER_RESULT], reason=df[self.HEADER_REASON])

        result_dict[self.HEADER_RESULT] = passfail
        result_dict[self.HEADER_REASON] = reason

        result_df = pd.DataFrame(result_dict, columns=list(result_dict.keys()),
                                 index=[0])
        return result_df

    def _flatten_passfail(self, passfail: pd.Series, reason: pd.Series) -> \
            t.Tuple[str, str]:

        for check in ["Invalid", "N/A", "Fail", "Pass"]:
            checked = passfail[passfail == check]
            if not checked.empty:
                return check, reason[checked.index[0]]
