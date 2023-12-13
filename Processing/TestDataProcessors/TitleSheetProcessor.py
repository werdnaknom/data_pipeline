import pandas as pd

from Processing import DataFrameProcessor

class TitleSheetProcessor(DataFrameProcessor):
    def __init__(self):
        super(TitleSheetProcessor, self).__init__()
        self.dataframe_name = "Title"

    def _process_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        return dataframe
