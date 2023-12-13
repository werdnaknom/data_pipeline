import pandas as pd

from Processing import DataFrameProcessor


class SequencingProcessor(DataFrameProcessor):

    def __init__(self):
        super(SequencingProcessor, self).__init__()
        self.dataframe_name = "Sequencing"

    def _process_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        return dataframe
