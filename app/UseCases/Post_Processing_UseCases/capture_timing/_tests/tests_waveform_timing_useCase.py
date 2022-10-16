from unittest import TestCase, mock
from pathlib import Path
import typing as t
import logging
import sys
import pickle

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

from basicTestCase.basic_test_case import BasicTestCase

from app.Repository.repository import Repository, MongoRepository
from app.shared.Entities.entities import WaveformEntity


def mock_load_waveforms(df) -> t.List[WaveformEntity]:
    wfs = []
    base_path = Path(r"C:\Users\ammonk\OneDrive - Intel "
                     r"Corporation\Desktop\Test_Folder\fake_uploads\post_processed_entities\VSD_Waveforms")
    wf_ids = df["waveform_id"].values
    for id in wf_ids:
        filename = f"{id}"
        wf_path = base_path.joinpath(filename)
        with open(wf_path, 'rb') as f:
            wf = pickle.load(f)
            wfs.append(wf)
    return wfs


class TestSequencingUseCase(BasicTestCase):
    logger_name = 'Waveform Sequencing Test'

    def _load_sequencing_pp_df(self) -> pd.DataFrame:
        df = pd.read_csv(r"C:\Users\ammonk\OneDrive - Intel "
                         r"Corporation\Desktop\Test_Folder\fake_uploads\island_rapids_pp_saved_df.csv")
        return df

    def _setUp(self):
        self.mock_repo = mock.MagicMock(Repository)
        # self.uc = WaveformSequencingUseCase(repo=self.mock_repo)
        self.test_df = self._load_sequencing_pp_df()

    def test_process_request(self):
        for filter, group_df in self.test_df.groupby(by=["capture", "runid"]):
            group_df.sort_values(by=["trace_order"], ascending=False,
                                      inplace=True)
            print(filter)
            wfs = mock_load_waveforms(df=group_df)
            break

        t0 = None
        for wf in wfs:
            if t0 == None:
                t0 = wf.x_axis_in_milliseconds()[wf.steady_state_index()]
            print(wf.descriptor, wf.steady_state_index(),
                  wf.x_axis_in_milliseconds()[wf.steady_state_index()] - t0)
            plt.plot(wf.x_axis_in_milliseconds(), wf.y_axis())

        plt.show()

    @mock.patch("app.UseCases.Post_Processing_UseCases"
                ".post_processing_use_case.PostProcessingUseCase."
                ".load_waveforms", side_effect=mock_load_waveforms)
    def test_process_request2(self, mock_load):
        # req = PostProcessingRequestObject(filters=[],
        #                                  df=self.test_df)

        # resp = self.uc.execute(request_object=req)
        wfs = mock_load_waveforms(df=self.test_df)
        plt.plot(wfs)
