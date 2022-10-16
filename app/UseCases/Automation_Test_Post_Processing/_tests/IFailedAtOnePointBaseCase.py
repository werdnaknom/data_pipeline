from unittest import mock
import typing as t
from pathlib import Path

import pandas as pd

from basicTestCase.basic_test_case import BasicTestCase

from app.CeleryTasks.cleanup_input_dataframe_tasks import waveform_cleanup, \
    WaveformDataFrameCleanUp, EthAgentDataFrameCleanup, traffic_cleanup
from app.CeleryTasks.update_repository_from_csv import \
    TrafficUpdateMongoRepositoryTask, traffic_update_mongo, \
    WaveformUpdateMongoRepositoryTask, waveform_update_mongo
from app.UseCases.Entity_Uploading.csv_to_repo_usecase import \
    CSVToRepoRequestObject
from app.UseCases.Automation_Tests_UseCases.automation_test_usecase import \
    AutomationTestRequestObject


class IFailedAtOncePointBaseCase(BasicTestCase):
    failure_name: str = ""
    BASE_DIRECTORY = r""
    DATACSV_NAME = "DATACSV.csv"
    USERINPUT_NAME = "USERINPUT.xlsx"
    PROCESSED_NAME = "PROCESSED.csv"
    AUTOMATION_TEST_DATAFOLDER = "Aux To Main"

    def build_processed_dataset(self):
        df = self._product_processed_df()
        self.logger.debug(f"-- Processed DF size: {df.shape}")

    def _product_processed_df(self) -> \
            pd.DataFrame:

        # Check if file exists
        base_path = Path(self.BASE_DIRECTORY)
        processed_df_path = base_path.joinpath(self.PROCESSED_NAME)

        exists = processed_df_path.exists()

        if exists:
            self.logger.debug(f"Loading existing processed file for test")
            df = pd.read_csv(processed_df_path)
            return df
        else:
            self.logger.debug(f"Building processed file for "
                              f"{self.failure_name}")
            # Grab the input and data dataframe paths
            raw_path = base_path.joinpath(self.DATACSV_NAME)
            raw_path_str = self._convert_existing_path_to_str(path=raw_path)
            input_path = base_path.joinpath(self.USERINPUT_NAME)
            input_path_str = self._convert_existing_path_to_str(path=input_path)

            # Clean and combine the two
            if self.AUTOMATION_TEST_DATAFOLDER == "EthAgent":
                path_str = self._clean_inputs_traffic(
                    config_path=input_path_str,
                    data_path=raw_path_str)
                # Update Mongo Repo
                df = self._mongo_update_traffic(df_path_str=path_str)
            else:
                path_str = self._clean_inputs_waveform(config_path=input_path,
                                                       data_path=raw_path)
                # Update Mongo Repo
                df = self._mongo_update_waveform(df_path_str=path_str)

            # Save DataFrame
            save_path = self._create_processed_saved_path()

            df.to_csv(save_path)
            return df

    def _convert_existing_path_to_str(self, path: Path) -> str:
        assert path.exists(), f"{path} must exist!"
        str_ver = str(path.resolve())
        return str_ver

    def _mongo_update_waveform(self, df_path_str) -> pd.DataFrame:
        request_obj = CSVToRepoRequestObject(df_path_str=df_path_str)
        updated_df_path_str = WaveformUpdateMongoRepositoryTask().run(
            request_object=request_obj)
        df = pd.read_pickle(updated_df_path_str)
        return df

    def _mongo_update_traffic(self, df_path_str) -> pd.DataFrame:
        request_obj = CSVToRepoRequestObject(df_path_str=df_path_str)
        updated_df_path_str = TrafficUpdateMongoRepositoryTask().run(
            request_object=request_obj)
        df = pd.read_pickle(updated_df_path_str)
        return df

    def _clean_inputs_waveform(self, config_path: str, data_path: str) -> str:
        cleaned_df_path_str = WaveformDataFrameCleanUp().run(
            config_path=config_path,
            data_path=data_path)
        return cleaned_df_path_str

    def _clean_inputs_traffic(self, config_path: str, data_path: str) -> str:
        cleaned_df_path_str = EthAgentDataFrameCleanup().run(
            config_path=config_path,
            data_path=data_path
        )
        return cleaned_df_path_str

    def _create_processed_saved_path(self) -> str:
        SAVE_SUFFIX = ".csv"
        base_path = Path(self.BASE_DIRECTORY)

        processed_path = base_path.joinpath(self.PROCESSED_NAME).with_suffix(
            SAVE_SUFFIX)

        return str(processed_path.resolve())

    def _validate_response(self, response):
        self.assertTrue(response)
        df_path = response.value

        self.assertIsInstance(df_path, Path)
        self.assertTrue(df_path.exists())
        self.assertEqual(df_path.suffix, ".xlsx")

    def _validate_dataframe(self, df_path: Path, expected_sheets: list,
                            filter_by: str):
        df_dict = pd.read_excel(df_path, sheet_name=None)

        self.assertEqual(len(df_dict.keys()), len(expected_sheets))

        expected_headers = self._filterby_headers(filter_by=filter_by)

        for sheet_name, df in df_dict.items():
            self.assertIn(sheet_name, expected_sheets)

            cols = df.columns
            for plot_header in self.PLOT_FIELDS:
                self.assertIn(plot_header, cols)
            for header in expected_headers:
                self.assertIn(header, cols)

    def _filterby_headers(self, filter_by: str):
        if filter_by == "default":
            filter_by = self.DEFAULT_FILTERBY
        if filter_by == "testpoint":
            headers = ["DUT", "PBA", "Rework", "DUT Serial", "Runid",
                       "Capture", "Testpoint"]
        if filter_by == "capture":
            headers = ["DUT", "PBA", "Rework", "DUT Serial", "Runid",
                       "Capture"]
        elif filter_by == "runid":
            headers = ["DUT", "PBA", "Rework", "DUT Serial", "Runid"]
        elif filter_by == "sample":
            headers = ["DUT", "PBA", "Rework", "DUT Serial"]
        elif filter_by == "rework":
            headers = ["DUT", "PBA", "Rework"]
        elif filter_by == "pba":
            headers = ["DUT", "PBA", ]
        elif filter_by == "dut":
            headers = ["DUT"]
        return headers

    def _AutomationTest_request_object(self, filter_by: str = "default"):
        input_df = self._product_processed_df()
        input_df = input_df[input_df["status_json_status"] == "Complete"]

        if filter_by == "default" or filter_by == self.DEFAULT_FILTERBY:
            input_df = input_df[
                input_df.capture.between(0, 3)]

        return AutomationTestRequestObject(df=input_df,
                                           filter_by=filter_by)

    def _test_filter(self, filter_by: str):
        req = self._AutomationTest_request_object(filter_by=filter_by)
        resp = self.uc.execute(request_object=req)

        print(resp)
        print(resp.value)

        self._validate_response(response=resp)

        self._validate_dataframe(df_path=resp.value,
                                 expected_sheets=self.EXPECTED_SHEETS,
                                 filter_by=filter_by)

        return resp.value
