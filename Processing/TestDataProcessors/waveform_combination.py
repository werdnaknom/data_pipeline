import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

from Processing import DataFrameProcessor

from Entities.WaveformFunctions.waveform_analysis import WaveformAnalysis


class WaveformCombinationProcessor(DataFrameProcessor):

    def __init__(self):
        super(WaveformCombinationProcessor, self).__init__()
        self.dataframe_name = "Combination Waveforms"

    def _process_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        # Group the DataFrame by 'Waveform' column
        grouped = dataframe.groupby('waveforms.testpoint')

        # Calculate the minimum, mean, and maximum values for 'Min' and 'Max' columns
        stats_df = grouped.agg({
            'waveforms.max': ['min', 'mean', 'max'],
            'waveforms.min': ['min', 'mean', 'max'],
            'waveforms.location': lambda x: list(x),
            'project': 'first'
        })

        # Flatten the multi-level column names
        stats_df.columns = [f"{col[0]}_{col[1]}" if col[1] in ['min', 'mean', 'max'] else col[0] for col in
                            stats_df.columns]
        stats_df = stats_df.reset_index()

        # for group, grouped_df in dataframe.groupby(by=["waveforms.testpoint", "runid"]):
        '''
        wa = WaveformAnalysis()
        for i, row in stats_df.iterrows():
            waveforms = row['waveforms.location']
            for wf_loc in waveforms:
                wf = wa.read_binary_waveform(wfm_path=Path(wf_loc), compressed=False)
                downsample_y = wa.min_max_downsample_1d(wf, size=600)
                plt.plot(downsample_y)
            #plt.show()
            plt.close()
        '''

        return stats_df
