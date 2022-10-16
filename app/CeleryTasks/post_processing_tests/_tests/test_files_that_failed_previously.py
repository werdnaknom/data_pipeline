import typing as t
import json
from collections import OrderedDict

import pandas as pd

from basicTestCase.basic_test_case import BasicTestCase

from app.CeleryTasks.post_processing_tests.load_profile import \
    LoadProfileTask, LoadProfileUseCase

from app.Repository.repository import MongoRepository


class LoadProfileSystemInfoProbesType1P0(BasicTestCase):

    def _load_input_paths(self):
        base_path = r"C:\Users\ammonk\OneDrive - Intel " \
                    r"Corporation\Desktop\Test_Folder\fake_uploads"
        csv_path = base_path + r"\MentorHarbor_aux_to_main_small.csv"
        userInput_path = base_path + r"\userInput.xlsx"

        return csv_path, userInput_path

    def test_system_info_json_probes_type(self):
        csv_path, userInput_path = self._load_input_paths()
        input_request = json.dumps({
            "data_file_path": csv_path,
            "user_input_file_path": userInput_path,
            'test_name': "Load Profile",
            "data_filename": "Test",
            "user_input_filename": "Test"
        })

        uc = LoadProfileTask()
        result = uc.run(request=input_request)

        self.assertIsInstance(result, dict)

        self.assertListEqual(["current", "total", "status", "result",
                              "filename"], list(result.keys()))

class LoadProfileTestLagsOut(BasicTestCase):

    def _load_input_paths(self):
            base_path = r"C:\Users\ammonk\OneDrive - Intel " \
                        r"Corporation\Desktop\Test_Folder\fake_uploads"
            csv_path = base_path + r"\MentorHarbor_aux_to_main.csv"
            userInput_path = base_path + r"\userInput.xlsx"

            return csv_path, userInput_path

    def test_lags_out(self):
        csv_path, userInput_path = self._load_input_paths()
        input_request = json.dumps({
            "data_file_path": csv_path,
            "user_input_file_path": userInput_path,
            'test_name': "Load Profile",
            "data_filename": "Test",
            "user_input_filename": "Test"
        })

        uc = LoadProfileTask()
        result = uc.run(request=input_request)

        self.assertIsInstance(result, dict)

        self.assertListEqual(["current", "total", "status", "result",
                              "filename"], list(result.keys()))

    def test_extract_request_paths(self):
        uc = LoadProfileTask()

        input_request = json.dumps({
            "data_file_path": "fake_path",
            "user_input_file_path": "fake_user",
            'test_name': "Load Profile",
            "data_filename": "Test",
            "user_input_filename": "Test"
        })

        x = uc.extract_request_paths(request=input_request)
        #print(x)

        self.assertDictEqual(x, {'test_name': 'Load Profile',
                                 'data_path': 'fake_path',
                                 'data_filename': 'Test',
                                 'config_path': 'fake_user',
                                 'config_filename': 'Test'})
