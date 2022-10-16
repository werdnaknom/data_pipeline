from unittest import TestCase, mock
import logging
import sys
import numpy as np

import mongomock

import pandas as pd


class TestAnalyzeWaveformRequestObject(TestCase):
    logger = logging.getLogger('RequestObjectTestLogger')
    logger.setLevel(level=logging.DEBUG)
    df = pd.read_csv(
        r'C:\Users\ammonk\Desktop\Test_Folder\fake_uploads\MentorHarbor_aux_to_main.csv')

    def setUp(self) -> None:
        self.hdlr = logging.StreamHandler(sys.stderr)
        self.logger.addHandler(hdlr=self.hdlr)

    def tearDown(self) -> None:
        self.logger.removeHandler(self.hdlr)

    def test_request_object_from_dataframe_row(self):
        from app.UseCases.Entity_Uploading.analyze_waveform_usecase import \
            AnalyzeWaveformRequestObject

        for i, row in self.df.iterrows():
            self.logger.debug("---" * 5)

            rq = AnalyzeWaveformRequestObject(df_row=row)

            self.logger.debug(msg=f"{rq.units}")
            self.assertEqual(rq.units, rq.probe_info["units"])
            self.assertIsInstance(rq.units, str)
            self.logger.debug(msg=f"{rq.test_category}")
            self.assertEqual(rq.test_category, row["test_category"])
            self.assertIsInstance(rq.test_category, str)
            self.logger.debug(msg=f"{rq.testpoint}")
            self.assertEqual(rq.testpoint, row["testpoint"])
            self.assertIsInstance(rq.testpoint, str)
            self.logger.debug(msg=f"{rq.scope_channel}")
            self.assertEqual(rq.scope_channel, row["scope_channel"])
            self.assertIsInstance(rq.scope_channel, int)
            self.logger.debug(msg=f"{rq.location}")
            self.assertEqual(rq.location, row['location'])
            self.assertIsInstance(rq.location, str)
            self.logger.debug(msg=f"{rq.capture}")
            self.assertEqual(rq.capture, row["capture"])
            self.assertIsInstance(rq.capture, int)
            self.logger.debug(msg=f"{rq.runid}")
            self.assertEqual(rq.runid, row["runid"])
            self.assertIsInstance(rq.runid, int)
            self.logger.debug(msg=f"{rq.x_increment}")
            self.assertEqual(rq.x_increment, row["capture_json_x_increment"])
            self.assertIsInstance(rq.x_increment, float)
            self.logger.debug(msg=f"{rq.compress}")
            if row["capture_json_compress"] == "TRUE":
                self.assertTrue(rq.compress)
            else:
                self.assertFalse(rq.compress)
            self.assertIsInstance(rq.compress, bool)
            self.logger.debug(msg=f"{rq.probe_info}")
            self.assertIsInstance(rq.probe_info, dict)
            self.logger.debug(msg=f"{rq.initial_x}")
            self.assertEqual(rq.initial_x, row["capture_json_initial_x"])
            self.assertIsInstance(rq.initial_x, float)


class TestAnalyzeWaveform(TestCase):
    logger = logging.getLogger('MongoTestLogger')
    logger.setLevel(level=logging.DEBUG)
    df = pd.read_csv(
        r'C:\Users\ammonk\Desktop\Test_Folder\fake_uploads\MentorHarbor_aux_to_main.csv')

    def setUp(self) -> None:
        self.hdlr = logging.StreamHandler(sys.stderr)
        self.logger.addHandler(hdlr=self.hdlr)

    def tearDown(self) -> None:
        self.logger.removeHandler(self.hdlr)

    def test_create_voltage_waveform(self):
        from app.UseCases.Entity_Uploading.analyze_waveform_usecase import \
            AnalyzeWaveformRequestObject, AnalyzeWaveformUseCase

        from app.shared.Entities.entities import WaveformEntity, TriStateType

        mock_repo = mock.Mock()
        mock_repo.find_waveform.return_value = {}

        RUNID = 87
        CAPTURE = 20

        uc = AnalyzeWaveformUseCase(repo=mock_repo)
        short_df = self.df[(self.df.runid == RUNID) &
                           (self.df.capture == CAPTURE)]
        for index, row in short_df.iterrows():
            rq = AnalyzeWaveformRequestObject(df_row=row)
            wave_entity = uc.create_voltage_waveform(request_object=rq)

            self.assertIsInstance(wave_entity, WaveformEntity)
            self.assertEqual(wave_entity.runid, RUNID)
            self.assertEqual(wave_entity.capture, CAPTURE)

            self.assertEqual(wave_entity.test_category,
                             row.test_category.lower().replace(" ", ""))
            self.assertEqual(wave_entity.location, row.location)
            self.assertEqual(wave_entity.testpoint, row.testpoint)
            self.assertEqual(wave_entity.edge, None)
            self.assertEqual(wave_entity.associated_rail, "")
            self.assertIsInstance(wave_entity._id, str)
            self.assertIsInstance(wave_entity.max, float)
            self.assertIsInstance(wave_entity.min, float)
            self.assertIsInstance(wave_entity.steady_state_min, float)
            self.assertIsInstance(wave_entity.steady_state_max, float)
            self.assertIsInstance(wave_entity.steady_state_mean, float)
            self.assertIsInstance(wave_entity.steady_state_pk2pk, float)

            self.assertIsInstance(wave_entity.downsample, list)
            self.assertIsInstance(wave_entity.downsample[0], np.ndarray)
            self.assertIsInstance(wave_entity.downsample[1], np.ndarray)
            self.assertIsInstance(wave_entity.edge, type(None))
            self.assertIsInstance(wave_entity.associated_rail, str)



            print(wave_entity)
    def test_create_current_waveform(self):
        from app.UseCases.Entity_Uploading.analyze_waveform_usecase import \
            AnalyzeWaveformRequestObject, AnalyzeWaveformUseCase

        from app.shared.Entities.entities import WaveformEntity

        mock_repo = mock.Mock()
        mock_repo.find_waveform.return_value = {}

        RUNID = 87
        CAPTURE = 20

        uc = AnalyzeWaveformUseCase(repo=mock_repo)
        short_df = self.df[(self.df.runid == RUNID) &
                           (self.df.capture == CAPTURE)]
        for index, row in short_df.iterrows():
            rq = AnalyzeWaveformRequestObject(df_row=row)
            wave_entity = uc.create_current_waveform(request_object=rq)

            self.assertIsInstance(wave_entity, WaveformEntity)
            self.assertEqual(wave_entity.runid, RUNID)
            self.assertEqual(wave_entity.capture, CAPTURE)

            self.assertEqual(wave_entity.test_category,
                             row.test_category.lower().replace(" ", ""))
            self.assertEqual(wave_entity.location, row.location)
            self.assertEqual(wave_entity.testpoint, row.testpoint)
            self.assertIsInstance(wave_entity._id, str)
            self.assertIsInstance(wave_entity.max, float)
            self.assertIsInstance(wave_entity.min, float)

            self.assertIsInstance(wave_entity.downsample, tuple)
            self.assertIsInstance(wave_entity.downsample[0], np.ndarray)
            self.assertIsInstance(wave_entity.downsample[1], np.ndarray)



            print(wave_entity)