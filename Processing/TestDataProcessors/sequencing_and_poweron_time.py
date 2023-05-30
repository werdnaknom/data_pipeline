import typing as t

import pandas as pd

from Processing import DataFrameProcessor


class TitleSheetProcessor(DataFrameProcessor):
    def __init__(self):
        super(TitleSheetProcessor, self).__init__()
        self.dataframe_name = "Title"

    def _process_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        return dataframe


class NoProcessor(DataFrameProcessor):

    def __init__(self):
        super(NoProcessor, self).__init__()
        self.dataframe_name = "Repository Data"

    def _process_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        return dataframe


class SequencingProcessor(DataFrameProcessor):

    def __init__(self):
        super(SequencingProcessor, self).__init__()
        self.dataframe_name = "Sequencing"

    def _process_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        return dataframe


class PowerOnTimeProcessor(DataFrameProcessor):

    def __init__(self):
        super(PowerOnTimeProcessor, self).__init__()
        self.dataframe_name = "Power-on Time"

    def _process_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        return dataframe
