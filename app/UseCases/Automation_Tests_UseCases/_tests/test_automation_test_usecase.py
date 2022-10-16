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

RAW_PATH = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's Code\unit_test_data\00_raw"
PROCESSED_PATH = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's " \
                 r"Code\unit_test_data\01_processed"
INPUT_PATH = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's Code\unit_test_data\00_userInput"


class AutomationTestBaseCase(BasicTestCase):
    TEST: str = None
    AUTOMATION_TEST: str = None
    DEFAULT_FILTERBY = "CHANGETHISTODEFAULT"
    PLOT_FIELDS = []
    EXPECTED_SHEETS = ["CHANGE THIS TO SHEETNAMES"]

    def build_processed_dataset(self):
        products = ["Island Rapids", "Albany Channel", "Bowman Flat",
                    "Campbell Pond", "Campbell Pond DP", "Clifton Channel",
                    "Edgewater Channel DP", "Empire Flat", "Fox Pond",
                    "Inner Channel", "Island Rapids", "Lewis Hill x8",
                    "Mentor Harbor", "Salem Channel", "Tacoma Rapids"]
        for product in products:
            df = self.product_processed_df(product=product)
            self.logger.debug(f"-- {product} Processed DF size: {df.shape}")

    def product_processed_df(self, product: str, filename_attr: str = "") -> \
            pd.DataFrame:

        # Check if file exists
        save_path, exists = self._get_save_path(product=product,
                                                filename_attr=filename_attr)
        if exists:
            self.logger.debug(f"Loading existing processed file for {product}")
            df = pd.read_csv(save_path)
            return df
        else:
            self.logger.debug(f"Building processed file for {product}")
            # Grab the input and data dataframe paths
            try:
                raw_path = self.product_raw_df_path(product=product)
            except AssertionError:
                self.logger.debug(f"-- DataCSV missing for {product}")
                return pd.DataFrame()
            try:
                input_path = self.product_input_df_path(product=product)
            except AssertionError:
                msg = f"-- InputXLSX missing for {product}"
                if filename_attr:
                    msg = msg + f", {filename_attr}"
                self.logger.debug(msg)
                return pd.DataFrame()

            # Clean and combine the two
            if self.AUTOMATION_TEST == "EthAgent":
                path_str = self._clean_inputs_traffic(config_path=input_path,
                                                      data_path=raw_path)
                # Update Mongo Repo
                df = self._mongo_update_traffic(df_path_str=path_str)
            else:
                path_str = self._clean_inputs_waveform(config_path=input_path,
                                                       data_path=raw_path)
                # Update Mongo Repo
                df = self._mongo_update_waveform(df_path_str=path_str)

            # Save DataFrame
            save_path, exists = self._get_save_path(product=product,
                                                    filename_attr=filename_attr)
            df.to_csv(save_path)
            return df

    def _product_data_file(self, base_path: Path, test: str, product: str,
                           suffix: str = ".csv") -> t.Tuple[str, bool]:
        test_path = base_path.joinpath(test)

        product_name = product.replace(" ", "_").lower()
        test_name = test.replace(" ", "_").lower()
        csv_name = f"{product_name}_{test_name}"

        product_path = test_path.joinpath(csv_name).with_suffix(suffix=suffix)

        if product_path.exists():
            exists = True
        else:
            exists = False

        return str(product_path.resolve()), exists

    def product_raw_df_path(self, product: str) -> str:
        raw_path = Path(RAW_PATH)
        path, exists = self._product_data_file(base_path=raw_path,
                                               test=self.AUTOMATION_TEST,
                                               product=product)
        self.assertTrue(exists, f"{path} should exist but doesn't!")
        return path

    def product_input_df_path(self, product: str):
        input_path = Path(INPUT_PATH)
        path, exists = self._product_data_file(base_path=input_path,
                                               test=self.TEST,
                                               product=product,
                                               suffix=".xlsx")
        self.assertTrue(exists, f"{path} should exist but doesn't!")
        return path

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

    def _get_save_path(self, product: str, filename_attr: str) \
            -> t.Tuple[str, bool]:
        SAVE_SUFFIX = ".csv"
        processed_path = Path(PROCESSED_PATH)

        path, exists = self._product_data_file(base_path=processed_path,
                                               product=product,
                                               suffix=SAVE_SUFFIX,
                                               test=self.TEST)
        if not filename_attr:
            return path, exists

        else:
            path = path.replace(SAVE_SUFFIX, "")
            path = path + "_" + filename_attr
            save_path = Path(path).with_suffix(suffix=SAVE_SUFFIX)

            if save_path.exists():
                exists = True
            else:
                exists = False
            return str(save_path.resolve()), exists

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

    def _AutomationTest_request_object(self, product: str,
                                       filter_by: str = "default"):
        input_df = self.product_processed_df(product=product)
        input_df = input_df[input_df["status_json_status"] == "Complete"]

        if filter_by == "default" or filter_by == self.DEFAULT_FILTERBY:
            input_df = input_df[
                input_df.capture.between(0, 3)]

        return AutomationTestRequestObject(df=input_df,
                                           filter_by=filter_by)

    def _test_product(self, product: str, filter_by: str):
        req = self._AutomationTest_request_object(product=product,
                                                  filter_by=filter_by)
        resp = self.uc.execute(request_object=req)

        print(resp)
        print(resp.value)

        self._validate_response(response=resp)

        self._validate_dataframe(df_path=resp.value,
                                 expected_sheets=self.EXPECTED_SHEETS,
                                 filter_by=filter_by)
