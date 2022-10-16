from unittest import TestCase, mock

import pandas as pd
import numpy as np

from faker import Faker

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
    SequencingResult


class TestTimingUseCase(BasicTestCase):
    logger_name = 'Waveform Timing Test'
    TEST_WAVEFORM_NAMES = ["0P9V_CVL1_AVDD", "0P9V_CVL2_AVDD", "3P3V_AUX",
                           "12V_MAIN", "DVDD_CVL1", "DVDD_CVL2"]

    def _load_sequencing_pp_df(self) -> pd.DataFrame:
        df = pd.read_csv(r"C:\Users\ammonk\OneDrive - Intel "
                         r"Corporation\Desktop\Test_Folder\fake_uploads\island_rapids_pp_saved_df.csv")
        return df

    def _load_waveform_df(self, waveform_name):
        filepath = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's " \
                   r"Code\unit_test_data\00_unit_test_specific" \
                   r"\Result_UseCases\waveform_sequencing\{" \
                   r"filename}.pkl".format(filename=waveform_name)
        df = pd.read_pickle(filepath)
        return df

    def test_init_WaveformTimingUseCase(self):
        waveform_df = self._load_waveform_df(
            waveform_name=self.TEST_WAVEFORM_NAMES[0])
        result = TestpointTimingResult2(df=waveform_df)
        self.assertIsInstance(result, pd.DataFrame)


"""

    def _create_fake_spec_max_failing_results(self, num_results: int = 8):
        faker = Faker()
        results = []
        for order in range(num_results):
            testpoint = faker.name()
            rand = np.random.random(2) * 10
            t0 = np.min(rand)
            min_time = np.max(rand) + t0
            max_time = min_time
            spec_min = t0
            spec_max = max_time - 1

            result = TestpointTimingResult(
                testpoint=testpoint, order=order, t0=t0, min_time=min_time,
                max_time=max_time, spec_min=spec_min, spec_max=spec_max,
                waveform_id=faker.name()
            )
            results.append(result)
        return results

    def _create_fake_spec_min_failing_results(self, num_results: int = 8):
        faker = Faker()
        results = []
        for order in range(num_results):
            testpoint = faker.name()
            rand = np.random.random(2) * 10
            t0 = np.max(rand)
            min_time = np.min(rand) + t0
            max_time = min_time
            spec_min = t0
            spec_max = max_time + np.random.random() * 10

            result = TestpointTimingResult(
                testpoint=testpoint, order=order, t0=t0, min_time=min_time,
                max_time=max_time, spec_min=spec_min, spec_max=spec_max,
                waveform_id=faker.name()
            )
            results.append(result)
        return results

    def _create_fake_passing_results(self, num_results: int = 8):
        faker = Faker()
        results = []
        for order in range(num_results):
            testpoint = faker.name()
            rand = np.random.random(2) * 10
            t0 = np.min(rand)
            min_time = np.max(rand) + t0
            max_time = min_time
            spec_min = t0
            spec_max = max_time + np.random.random() * 10

            result = TestpointTimingResult(
                testpoint=testpoint, order=order, t0=t0, min_time=min_time,
                max_time=max_time, spec_min=spec_min, spec_max=spec_max,
                waveform_id=faker.name()
            )
            results.append(result)
        return results

    def test_group_add_passing_result(self):
        df = self._load_sequencing_pp_df()
        group = SequencingCaptureResult(df=df)

        expected_results = self._create_fake_passing_results(num_results=8)
        for passing in expected_results:
            group.add_result(passing)

        self.assertListEqual(expected_results, group.results)
        self.assertEqual(len(expected_results), len(group.results))

    def test_group_passing_result(self):
        df = self._load_sequencing_pp_df()
        group = SequencingCaptureResult(df=df)

        num_results = 8

        for passing in self._create_fake_passing_results(
                num_results=num_results):
            group.add_result(passing)

        result = group.to_result()
        # print(result)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(num_results, len(result))

        self.assertEqual(result["Result"].unique(), "Pass")
        self.assertEqual(list(result["Group Result"].values),
                         ["Pass" for _ in range(num_results)])

    def test_group_max_failing_result(self):
        df = self._load_sequencing_pp_df()
        group = SequencingCaptureResult(df=df)

        num_results = 8

        for r in self._create_fake_spec_max_failing_results(
                num_results=num_results):
            group.add_result(r)
        for r in self._create_fake_passing_results(
                num_results=num_results):
            group.add_result(r)

        result = group.to_result()
        # print(result)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(num_results * 2, len(result))

        for passfail in ["Pass", "Fail"]:
            self.assertIn(passfail, result['Result'].unique())
        self.assertEqual(list(result["Group Result"].values),
                         ["Fail" for _ in range(num_results * 2)])

    def test_group_min_failing_result(self):
        df = self._load_sequencing_pp_df()
        group = SequencingCaptureResult(df=df)

        num_results = 8

        for r in self._create_fake_spec_min_failing_results(
                num_results=num_results):
            group.add_result(r)
        for r in self._create_fake_passing_results(
                num_results=num_results):
            group.add_result(r)

        result = group.to_result()
        # print(result)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(num_results * 2, len(result))

        for passfail in ["Pass", "Fail"]:
            self.assertIn(passfail, result['Result'].unique())
        self.assertEqual(list(result["Group Result"].values),
                         ["Fail" for _ in range(num_results * 2)])

    def test_group_traceorder(self):
        df = pd.read_excel(r'C:\Users\ammonk\OneDrive - Intel '
                           r'Corporation\Desktop\Test_Folder\fake_uploads\fake_results\AutomationTest_Oct-01_223127.xlsx')
        # print(df)

        print(df.groupby(by=["testpoint", "order"]).agg({
            "min time (ms)": ['mean', 'min', 'max'],
            "max time (ms)": ['mean', 'min', 'max']}))

    def test_group_gradeing(self):
        df = pd.read_excel(r'C:\Users\ammonk\OneDrive - Intel '
                           r'Corporation\Desktop\Test_Folder\fake_uploads\fake_results\AutomationTest_Oct-01_223127.xlsx')
        df = df.head(8)

        df = df.sort_values(by="min time (ms)")
    
"""
