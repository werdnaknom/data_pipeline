import pandas as pd

from Processing import DataFrameProcessor



class NoProcessor(DataFrameProcessor):

    def __init__(self):
        super(NoProcessor, self).__init__()
        self.dataframe_name = "Repository Data"

    def _process_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        return dataframe
