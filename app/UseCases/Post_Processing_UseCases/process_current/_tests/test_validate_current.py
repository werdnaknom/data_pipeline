from unittest import mock
from pathlib import Path
import pickle

import pandas as pd
import matplotlib.pyplot as plt

from basicTestCase.basic_test_case import BasicTestCase

from app.shared.Responses.response import ResponseSuccess

from app.Repository.repository import Repository

from app.UseCases.Post_Processing_UseCases.process_current \
    .validate_current_use_case import CurrentProcessingUseCase, \
    PostProcessingRequestObject
from app.UseCases.Post_Processing_UseCases.process_current \
    .validate_current_results import CurrentProcessResultRow
from app.shared.Entities.entities import *


def mock_load_waveforms(df) -> t.List[WaveformEntity]:
    wfs = []
    base_path = Path(r"C:\Users\ammonk\OneDrive - Intel "
                     r"Corporation\Desktop\Test_Folder\fake_uploads\post_processed_entities\LoadProfile_Waveforms")
    wf_ids = df["waveform_id"].values
    for id in wf_ids:
        filename = f"{id}.pkl"
        wf_path = base_path.joinpath(filename)
        with open(wf_path, 'rb') as f:
            wf_dict = pickle.load(f)
            wfs.append(WaveformEntity.from_dict(wf_dict))
    return wfs


class ValidateCurrentTestCase(BasicTestCase):

    def _setUp(self):
        self.mock_repo = mock.MagicMock(Repository)
        self.uc = CurrentProcessingUseCase(repo=self.mock_repo)
        self.req = PostProcessingRequestObject(df=
                                               self._helper_load_post_processed_df(),
                                               filters=[])

    @mock.patch("app.UseCases.Post_Processing_UseCases.process_current"
                ".validate_current_use_case.CurrentProcessingUseCase"
                ".load_waveforms", side_effect=mock_load_waveforms)
    def test_post_process(self, mock_waveforms):
        # mock_waveforms.side_effect=mock_load_waveforms
        resp = self.uc.post_process(request_object=self.req)
        self.assertIsInstance(resp, pd.DataFrame)

    def test_mock_pivot_table(self):
        df = self.req.df
        pivot = df.pivot_table(columns=["dut", "pba"], margins=True)
        print(pivot)

    def test_mock_stack(self):
        df = self.req.df
        stack = df.stack()
        unstacked0 = stack.unstack(level=0)  # Transpose
        unstacked1 = stack.unstack(level=1)  # Goes back to normal
        print(stack)

    def test_mock_melt(self):
        df = self.req.df

        cheese = df.melt(id_vars=["dut", 'pba', 'capture'])
        print(cheese)
