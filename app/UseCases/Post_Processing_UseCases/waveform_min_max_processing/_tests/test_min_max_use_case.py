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

from app.UseCases.Post_Processing_UseCases.waveform_min_max_processing \
    .min_max_use_case import WaveformProcessingUseCase, \
    PostProcessingRequestObject


def mock_load_waveforms(df) -> t.List[WaveformEntity]:
    wfs = []
    base_path = Path(r"C:\Users\ammonk\OneDrive - Intel "
                     r"Corporation\Desktop\Test_Folder\fake_uploads\post_processed_entities\Waveforms")
    wf_ids = df["waveform_id"].values
    for id in wf_ids:
        filename = f"{id}.pkl"
        wf_path = base_path.joinpath(filename)
        with open(wf_path, 'rb') as f:
            wf_dict = pickle.load(f)
            wfs.append(WaveformEntity.from_dict(wf_dict))
    return wfs


class TestSequencingUseCase(BasicTestCase):
    logger_name = 'Waveform Sequencing Test'

    def _load_pp_df(self) -> pd.DataFrame:
        df = pd.read_csv(r"C:\Users\ammonk\OneDrive - Intel "
                         r"Corporation\Desktop\Test_Folder\fake_uploads\island_rapids_pp_saved_df.csv")
        return df

    def _setUp(self):
        self.mock_repo = mock.MagicMock(Repository)
        self.uc = WaveformProcessingUseCase(repo=self.mock_repo)
        self.test_df = self._load_pp_df()

    '''
    @mock.patch(
        "app.UseCases.Post_Processing_UseCases.waveform_min_max_processing.min_max_use_case.WaveformProcessingUseCase.load_waveforms",
        side_effect=mock_load_waveforms)
    def test_process_request(self, mock_load):
        req = PostProcessingRequestObject(filters=[],
                                          df=self.test_df)
        resp = self.uc.execute(request_object=req)
    '''

    def test_process_request(self):
        req = PostProcessingRequestObject(filters=[],
                                          df=self.test_df)
        uc = WaveformProcessingUseCase(repo=MongoRepository())
        resp = uc.execute(request_object=req)

    def test_make_plot(self):
        base_path = Path(r"C:\Users\ammonk\OneDrive - Intel Corporation\Desktop\Test_Folder\fake_uploads\post_processed_entities\VSD_Waveforms")
        for wf_path in base_path.iterdir():
            if wf_path.suffix == "":
                with open(wf_path, 'rb') as f:
                    wf = pickle.load(f)

                    self.uc.make_plot(waveforms=[wf], spec_max=1,
                                      spec_min=0.8, testpoint=wf.testpoint)




    def test_filterDF(self):
        filt_df = self.uc.filterDf(raw_data=self.test_df)
        print(filt_df)

    def test_post_process(self):
        req = PostProcessingRequestObject(df=self.test_df,
                                          filters=[])
        uc = WaveformProcessingUseCase(repo=MongoRepository())
        result = uc.post_process(request_object=req)
        print(result)
        # result = self.uc.post_process(request_object=req)
        # print(result)

    def test_testpoint_specs(self):
        filtdf = self.uc.filter_df(self.test_df)
        values = self.uc.get_testpoint_specs(testpoint="3P3V", df=filtdf)

        self.logger.debug(f"{values}")
        self.assertEqual(4, len(values))

        self.assertEqual((False, 2, 4, 0.5), values)

    def test_filter_df(self):
        df = self.test_df
        filt_df = self.uc.filter_df(raw_df=df)
        self.assertIsInstance(filt_df, pd.DataFrame)

        tsc = self.uc._test_specific_columns()
        for column in tsc:
            self.assertIn(column, filt_df.columns)

        self.assertIn("ch2_group", filt_df.columns)
        self.assertNotIn("file_capture_capture.png", filt_df.columns)

    def test_make_results_df(self):
        filt_df = self.uc.filter_df(raw_df=self.test_df)
        uc = WaveformProcessingUseCase(repo=MongoRepository())
        df = uc.make_results_df(filtered_df=filt_df,
                                merge_columns=["waveform_id"])

        print(df)
