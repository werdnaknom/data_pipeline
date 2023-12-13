import typing as t
from abc import ABC
from dataclasses import dataclass

import numpy as np
import pandas as pd

from Entities.Entities import WaveformEntity
from Processing import DataFrameProcessor


class PowerOnTimeProcessor(DataFrameProcessor):

    def __init__(self):
        super(PowerOnTimeProcessor, self).__init__()
        self.dataframe_name = "Power-on Time"

    def _process_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        return dataframe
