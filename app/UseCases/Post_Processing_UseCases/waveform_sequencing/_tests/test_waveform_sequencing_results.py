from unittest import TestCase, mock
from collections import OrderedDict

import pandas as pd
import numpy as np

from faker import Faker
import random
import pickle

from basicTestCase.basic_test_case import BasicTestCase

from app.Repository.repository import Repository, MongoRepository

from app.UseCases.Post_Processing_UseCases.waveform_sequencing \
    .waveform_sequencing_use_case import WaveformSequencingUseCase, \
    PostProcessingRequestObject

from app.UseCases.Post_Processing_UseCases.waveform_sequencing \
    .waveform_sequencing_results import SequencingCaptureResult, \
    TestpointTimingResult

from app.UseCases.Post_Processing_UseCases.waveform_sequencing \
    .waveform_sequencing_results2 import TestpointTimingResult2, \
    SequencingResult, TraceOrderGroup


class TestTimingResult(BasicTestCase):
    logger_name = 'Waveform Timing Test'
    TEST_WAVEFORM_NAMES = ["0P9V_CVL1_AVDD", "0P9V_CVL2_AVDD", "3P3V_AUX",
                           "12V_MAIN", "DVDD_CVL1", "DVDD_CVL2"]

    def _load_sequencing_pp_df(self) -> pd.DataFrame:
        df = pd.read_csv(r"C:\Users\ammonk\OneDrive - Intel "
                         r"Corporation\Desktop\Test_Folder\fake_uploads\island_rapids_pp_saved_df.csv")
        return df

    def _load_waveform_df(self, waveform_name):
        filepath = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's " \
                   r"Code\unit_test_data\99_unit_test_specific" \
                   r"\Result_UseCases\waveform_sequencing\{filename}.pkl".format(
            filename=waveform_name)
        df = pd.read_pickle(filepath)
        return df

    def test_init_WaveformTiming(self):
        for waveform in self.TEST_WAVEFORM_NAMES:
            waveform_df = self._load_waveform_df(waveform_name=waveform)
            result = TestpointTimingResult2(df=waveform_df)

            self.assertIsInstance(result, TestpointTimingResult2)
            self.assertIsInstance(result.testpoint, str)
            self.assertEqual(result.testpoint, waveform)
            self.assertIsInstance(result.mean_timing, float)
            self.assertIsInstance(result.mode_timing, float)
            self.assertIsInstance(result.max_timing, float)
            self.assertIsInstance(result.min_timing, float)
            self.assertIsInstance(result.get_spec_timing(), float)
            self.assertIsInstance(result.get_spec_trace_order(), int)
            output_pickle = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's " \
                            r"Code\unit_test_data\99_unit_test_specific" \
                            r"\Result_UseCases\waveform_sequencing" \
                            r"\{testpoint}_result.pkl".format(
                testpoint=result.testpoint)
            pickle.dump(result, open(output_pickle, 'wb'))


class TestSequencingResult(BasicTestCase):
    logger_name = 'Waveform Sequencing Test'

    def _setUp(self):
        self.input_df = self._load_sequencing_input_df()

    def _load_sequencing_input_df(self):
        INPUT_PATH = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's Code\unit_test_data\99_unit_test_specific\Result_UseCases\waveform_sequencing\input_df.pkl"
        return pd.read_pickle(INPUT_PATH)

    def test_init_sequencing_result(self):
        input_df = self._load_sequencing_input_df()
        seq = SequencingResult(df=input_df)

        self.assertIsInstance(seq.df, pd.DataFrame)
        self.assertIsInstance(seq.tOrderGroups, list)

    def test_reorder_testpoints_by_expected_order(self):

        input_df = self._load_sequencing_input_df()
        expected_order = {
            0: ["12V_MAIN", "3P3V_AUX"],
            1: ["DVDD_CVL2", "DVDD_CVL1"],
            2: ["0P9V_CVL1_AVDD", "0P9V_CVL2_AVDD"],
        }
        for x in range(0, 10):
            randomized_df = input_df.sample(frac=1).reset_index(drop=True)
            self.logger.debug(f"TRY:{x}\n "
                              f"{randomized_df.head(5)}")
            seq = SequencingResult(df=randomized_df)

            order = seq._reorder_testpoints_by_expected_order()
            self.assertIsInstance(order, list)
            self.assertEqual(len(order), 3)
            previous_spec = -99
            for i, x in enumerate(seq._reorder_testpoints_by_expected_order()):
                self.logger.debug(f"{x.order}, {i}, {x.df.testpoint.unique()}")
                self.assertIsInstance(x, TraceOrderGroup)
                self.assertEqual(x.order, i)
                self.assertIsInstance(x.df, pd.DataFrame)
                current_poweron = x.df["power_on_time_spec"].unique()
                self.assertEqual(len(current_poweron), 1)
                current_poweron = current_poweron[0]
                self.assertGreater(current_poweron, previous_spec)
                previous_spec = current_poweron

                for testpoint in x.df.testpoint.unique():
                    self.assertIn(testpoint, expected_order[i])

    def test_cleanup_dataframe(self):
        seq = SequencingResult(df=self.input_df)
        cleanup_df = seq._cleanup_dataframe(df=self.input_df)

        expected_columns = ["testpoint", "trace_order", "power_on_time_spec",
                            "poweron_index", "capture_t0", "t0_to_poweron",
                            "total_poweron_time", "runid", "capture"]

        self.assertIsInstance(cleanup_df, pd.DataFrame)

        # Verifies the dataframe was sorted by increasing power_on_time_spec
        self.assertTrue(cleanup_df[
                            "power_on_time_spec"].is_monotonic_increasing)
        for col in cleanup_df.columns:
            self.logger.debug(f"COLUMN: {col}")
            self.assertIn(col, expected_columns)

    def test_sequencing_fail_metric(self):
        seq = SequencingResult(df=self.input_df)

        result = seq.sequencing_fail_metric()

        self.assertEqual(result, ("Pass", ""))

    def test_pass_fail(self):

        seq = SequencingResult(df=self.input_df)

        result = seq.passfail()

        self.logger.debug(f"RESULT: {result}")
        self.assertIsInstance(result, OrderedDict)

        expected_result = OrderedDict(
            [('Mean Timing: 3P3V_AUX (1)', -22.184053302798198),
             ('Mean Timing: 12V_MAIN (3)', 0.0),
             ('Mean Timing: DVDD_CVL1 (13)', 14.105265210138096),
             ('Mean Timing: DVDD_CVL2 (14)', 13.931195737549182),
             ('Mean Timing: 0P9V_CVL1_AVDD (15)', 18.032643759448337),
             ('Mean Timing: 0P9V_CVL2_AVDD (16)', 17.402163255063936),
             ('Sequencing Result', 'Pass'), ('Sequencing Reason', '')])

        self.assertDictEqual(expected_result, result)
