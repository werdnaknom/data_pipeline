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

from app.UseCases.Post_Processing_UseCases.waveform_power.waveform_power_use_case import \
    WaveformEdgePowerUseCase, PostProcessingRequestObject


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


class WaveformPowerUseCase(BasicTestCase):
    logger_name = 'Waveform Power UseCase'

    def _setUp(self):
        self.mock_repo = mock.MagicMock(Repository)
        self.uc = WaveformEdgePowerUseCase(repo=self.mock_repo)
        self.test_df = self._helper_load_post_processed_df()

    @mock.patch("app.UseCases.Post_Processing_UseCases.waveform_power"
                ".waveform_power_use_case.WaveformEdgePowerUseCase"
                ".load_waveforms", side_effect=mock_load_waveforms)
    def test_process_request(self, mock_load):
        req = PostProcessingRequestObject(filters=[],
                                          df=self.test_df)

        resp = self.uc.execute(request_object=req)
