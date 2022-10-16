from unittest import mock
from collections import OrderedDict
import datetime
import json

import pandas as pd
from faker import Faker

from basicTestCase.basic_test_case import BasicTestCase

from app.CeleryTasks.post_processing_tests.post_processing_task import \
    EthAgentDataFrameCleanup, WaveformDataFrameCleanUp


class TestCleanupPostProcessingUseCase(BasicTestCase):

    def _setUp(self):
        self.uc = WaveformDataFrameCleanUp()

        base_path = r"C:\Users\ammonk\OneDrive - Intel " \
                    r"Corporation\Desktop\Test_Folder\fake_uploads"
        self.data_path = base_path + r"\island_rapids_aux_to_main.csv"
        self.config_path = base_path + r"\userInput_IslandRapids.xlsx"

    def _helper_load_config_dict(self):
        config_dict = self.uc.load_dataframe_from_xlsx(
            xlsx_path=self.config_path)
        return config_dict

    def _helper_load_csv_df(self):
        data_df = self.uc.load_dataframe_from_csv(csv_path=self.data_path)
        return data_df


class TestWaveformCleanup(TestCleanupPostProcessingUseCase):

    def test_load_dataframe_from_xlsx(self):
        df_dict = self.uc.load_dataframe_from_xlsx(xlsx_path=self.config_path)

        self.assertIsInstance(df_dict, dict)
        EXPECTED_KEYS = ["Edge Channels", "On-Board Rails",
                         "Rails to Rename", "Sequencing", "Timing"]
        for key, value in df_dict.items():
            self.assertIn(key, EXPECTED_KEYS)
            self.assertIsInstance(value, pd.DataFrame)

    def test_load_dataframe_from_csv(self):
        df = self.uc.load_dataframe_from_csv(csv_path=self.data_path)

        self.assertIsInstance(df, pd.DataFrame)

    def test_sequencing_sheetname(self):
        data_df = self._helper_load_csv_df()
        config_dict = self._helper_load_config_dict()

        self.uc.sequencing_sheetname(config_dict=config_dict,
                                     data_df=data_df)

        self.assertIn("trace_order", list(data_df.columns))
        self.assertIn("power_on_time_spec", list(data_df.columns))

        self.assertTrue(data_df['trace_order'].notnull().all())
        self.assertTrue(data_df['power_on_time_spec'].notnull().all())

    def test_timing_sheet_name(self):
        data_df = self._helper_load_csv_df()
        config_dict = self._helper_load_config_dict()

        self.uc.timing_sheetname(config_dict=config_dict,
                                 data_df=data_df)

        self.assertIn("to_rail", list(data_df.columns))
        self.assertIn("to_rail_timing_spec", list(data_df.columns))


class TestEthAgentCleanUp(TestCleanupPostProcessingUseCase):

    def _setUp(self) -> None:
        self.uc = EthAgentDataFrameCleanup()

        base_path = r"C:\Users\ammonk\OneDrive - Intel " \
                    r"Corporation\Desktop\Test_Folder\fake_uploads"
        self.data_path = base_path + r"\mentor_harbor_ethagent.csv"
        self.config_path = base_path + r"\mentor_harbor_userInput.xlsx"

    def test_load_dataframe_from_xlsx(self):
        df_dict = self.uc.load_dataframe_from_xlsx(xlsx_path=self.config_path)

        self.assertIsInstance(df_dict, dict)
        EXPECTED_KEYS = ["BER"]
        for key, value in df_dict.items():
            self.assertIn(key, EXPECTED_KEYS)
            self.assertIsInstance(value, pd.DataFrame)

    def test_load_dataframe_from_csv(self):
        df = self.uc.load_dataframe_from_csv(csv_path=self.data_path)

        self.assertIsInstance(df, pd.DataFrame)

    def test_BER_sheet_name(self):
        data_df = self._helper_load_csv_df()
        config_dict = self._helper_load_config_dict()

        self.uc.ber_sheetname(config_dict=config_dict,
                              data_df=data_df)

        self.assertIn("specified_ber", list(data_df.columns))
        self.assertIn("module", list(data_df.columns))
        self.assertIn("target_confidence", list(data_df.columns))

