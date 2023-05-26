import pandas as pd

from Processing.processing_usecase import ProcessingUseCase
from multiprocessing import Pool


class WaveformProcessingUseCase(ProcessingUseCase):

    def multiprocess_process_image(self, dataframe: pd.DataFrame):
        with Pool() as pool:
            results = pool.map(self.process_image, dataframe.iterrows())
        return results

    def create_excel_sheets(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        pass

    def process_image(self, row):
        file_path = row['waveform.location']
        pass
