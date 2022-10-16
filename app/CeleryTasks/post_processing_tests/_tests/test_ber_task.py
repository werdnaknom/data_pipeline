import typing as t
import json
from collections import OrderedDict
from pathlib import Path

import pandas as pd

from basicTestCase.basic_test_case import BasicTestCase

from app.CeleryTasks.post_processing_tests.ber import \
    bit_error_ratio_task, BitErrorRatioTask

from celery_worker import celeryapp

from app.Repository.repository import MongoRepository


class VerifyBERWorksCorrectly(BasicTestCase):
    BASE = Path(
        r'C:\Users\ammonk\OneDrive - Intel Corporation\Desktop\Test_Folder\fake_uploads\all_uploads\EthAgent')
    TEST_NAME = "bit_error_ratio"
    TEST_CLASS = BitErrorRatioTask

    def _setUp(self):
        self.task = bit_error_ratio_task

    def _product_files(self, product_name):
        data_fmt = f"{product_name}_ethagent.csv".replace(" ", "_").lower()
        csv_path = self.BASE.joinpath(data_fmt)
        userInput_fmt = f"{product_name}_userInput.xlsx"
        userInput_path = self.BASE.joinpath("Inputs").joinpath(userInput_fmt)

        return csv_path, userInput_path

    def _build_request_json(self, product_name) -> json:
        csv_path, userInput_path = self._product_files(
            product_name=product_name)
        request_json = json.dumps({"test_name": self.TEST_NAME,
                                   "data_filename": csv_path.name,
                                   "data_file_path": str(csv_path),
                                   "user_input_filename": userInput_path.name,
                                   "user_input_file_path": str(userInput_path)})
        return request_json

    def start_product_task(self, product_name: str):
        request_json = self._build_request_json(product_name=product_name)
        self.logger.debug(f"Starting {product_name}: {request_json}")
        task = celeryapp.send_task(name=self.TEST_NAME,
                                   kwargs={"request": request_json})
        self.logger.debug(f"Task started: {task}")
        result = task.get()
        print(result)

    def start_product_test(self, product_name:str):
        request_json = self._build_request_json(product_name=product_name)
        self.logger.debug(f"Starting {product_name}: {request_json}")

        test = self.TEST_CLASS()
        test.run(request=request_json)


    def test_mentor_harbor_task(self):
        product_name = "mentor_harbor"
        self.start_product_task(product_name=product_name)

    def test_mentor_harbor_test(self):
        product_name = "mentor_harbor"
        self.start_product_test(product_name=product_name)

    def test_missing_sheetname(self):
        self.fail()
