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

from app.UseCases.Post_Processing_UseCases.waveform_sequencing \
    .waveform_sequencing_use_case import WaveformSequencingUseCase, \
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

    def _load_sequencing_pp_df(self) -> pd.DataFrame:
        df = pd.read_csv(r"C:\Users\ammonk\OneDrive - Intel "
                         r"Corporation\Desktop\Test_Folder\fake_uploads\island_rapids_pp_saved_df.csv")
        return df

    def _setUp(self):
        self.mock_repo = mock.MagicMock(Repository)
        self.uc = WaveformSequencingUseCase(repo=self.mock_repo)
        self.test_df = self._load_sequencing_pp_df()

    @mock.patch("app.UseCases.Post_Processing_UseCases"
                ".post_processing_use_case.PostProcessingUseCase."
                ".load_waveforms", side_effect=mock_load_waveforms)
    def test_process_request(self, mock_load):
        req = PostProcessingRequestObject(filters=[],
                                          df=self.test_df)

        resp = self.uc.execute(request_object=req)

    def test_filterDF(self):
        filt_df = self.uc.filterDf(raw_data=self.test_df)
        print(filt_df)

    def test_targetFound(self):
        # targetFound = self.uc.targetFound(window=, target=)
        targetVal = 1.5
        wfs = self._helper_load_waveforms()
        wf = wfs[3]
        ser = pd.Series(wf.y_axis())
        temp = ser.rolling(2).apply(self.uc.targetFound, args=(targetVal,),
                                    raw=True)
        targets = np.where(temp.notnull())
        if targets[0].shape[0] == 0:
            print(0)

        print(targets[0][0])
        print(temp)

    def test_filter_by_temperature(self):
        repo = MongoRepository()
        df = self._load_sequencing_pp_df()

        runids = df.runid.unique()

        capture = repo.find_waveform_captures_many(runid=runids[0], test="Aux To Main")
        print(len(capture))
        capture = repo.find_waveform_captures_many(runid=runids[0], test="Aux To Main",
                                                   additional_filters={
                                              "environment.chamber_setpoint":
                                                  25})
        print(len(capture))
        capture = repo.find_waveform_captures_many(runid=runids[0], test="Aux To Main",
                                                   additional_filters={
                                              "environment.chamber_setpoint": 25,
                                              "environment.power_supply_channels.slew_rate": 200,
                                          })
        print(len(capture))

    # def test_passFail(self):
    #    self.uc =

    def test_post_process(self):
        req = PostProcessingRequestObject(df=self.test_df,
                                          filters=[])
        uc = WaveformSequencingUseCase(repo=MongoRepository())
        result = uc.post_process(request_object=req)
        print(result)
        # result = self.uc.post_process(request_object=req)
        # print(result)

    def test_slew_rate_grouping(self):
        filt_df = self.uc.filter_df(raw_df=self.test_df)
        slew_rates = [200, 1000, 5000, 10000, 26400]
        for slew in slew_rates:
            result = self.uc.filter_df_by_slewrate(filtered_df=filt_df,
                                                   slew_rate=slew, group="Main")

            self.assertIsInstance(result, pd.DataFrame)

            self.assertEqual(result["ch1_slew"].unique(), [slew])
            self.assertEqual(len(result), len(filt_df) // len(slew_rates))

    def test_testpoint_specs(self):
        filtdf = self.uc.filter_df(self.test_df)
        values = self.uc.get_testpoint_specs(testpoint="3P3V", df=filtdf)

        self.logger.debug(f"{values}")
        self.assertEqual(4, len(values))

        self.assertEqual((False, 2, 4, 0.5), values)

    def test_retrieve_spec_target(self):
        df = self.test_df

        result = self.uc._spec_target(testpoint="3P3V", filtered_df=df)

        self.logger.debug(f"spec target returned: {result}")

        self.assertEqual(4, result)
        self.assertIsInstance(result, float)

    def test_trace_order(self):
        df = self.test_df
        expected_order = ["12V_EDGE",
                          "3P3V",
                          "QSFP_1_3P3V_TX",
                          "QSFP_1_3P3V_RX",
                          "QSFP_1_3P3V_VCC",
                          "QSFP_0_3P3V_TX",
                          "QSFP_0_3P3V_RX",
                          "QSFP_0_3P3V_VCC",
                          "1P8V_VDDH_CVL1",
                          "1P8V_VDDH_CVL2",
                          "DVDD_CVL1",
                          "DVDD_CVL2",
                          "0P9V_CVL1_AVDD",
                          "0P9V_CVL2_AVDD",
                          "0P9V_CVL1_AVDD_ETH",
                          "0P9V_CVL1_AVDD_PCIE",
                          "0P9V_CVL1_AVDD_PLL",
                          "0P9V_CVL2_AVDD_ETH",
                          "0P9V_CVL2_AVDD_PCIE",
                          "0P9V_CVL2_AVDD_PLL",
                          "1P1V_AVDDH",
                          "ALL_PWR_OK"]
        traceOrder = self.uc.get_trace_order(df=df)

        self.assertIsInstance(traceOrder, list)
        self.assertListEqual(expected_order, traceOrder)

    def test_filter_df(self):
        df = self.test_df
        filt_df = self.uc.filter_df(raw_df=df)
        self.assertIsInstance(filt_df, pd.DataFrame)

        tsc = self.uc._test_specific_columns()
        for column in tsc:
            self.assertIn(column, filt_df.columns)

        self.assertIn("ch2_group", filt_df.columns)
        self.assertNotIn("file_capture_capture.png", filt_df.columns)

    def test_get_main_slew_rates(self):
        filt_df = self.uc.filter_df(self.test_df)
        slews = self.uc.get_unique_slew_rates(input_df=filt_df)

        self.logger.debug(f"slews returned: {slews}")

        expected_slews = [200, 1000, 5000, 10000, 26400]
        for slew in expected_slews:
            self.assertIn(slew, slews)

        self.assertEqual(len(expected_slews), len(slews))

    def test_get_temperatures(self):
        filt_df = self.uc.filter_df(self.test_df)
        temps = self.uc.get_unique_temperatures(filtered_df=filt_df)

        self.logger.debug(f"temps returned: {temps}")

        expected_temps = [0, 25, 60]
        for value in temps:
            self.assertIn(value, expected_temps)

        self.assertEqual(len(expected_temps), len(temps))

    def test_get_main_voltages(self):
        filt_df = self.uc.filter_df(self.test_df)
        result = self.uc.get_main_voltages(filtered_df=filt_df)

        self.logger.debug(f"returned: {result}")

        expected_result = [11., 12., 13.]
        for value in result:
            self.assertIn(value, expected_result)

        self.assertEqual(len(expected_result), len(result))

    def test_make_results_df(self):
        filt_df = self.uc.filter_df(raw_df=self.test_df)
        uc = WaveformSequencingUseCase(repo=MongoRepository())
        df = uc.make_results_df(filtered_df=filt_df,
                                     merge_columns=["waveform_id"])

        print(df)
