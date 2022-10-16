from unittest import mock
from collections import OrderedDict
import datetime
import json
from pathlib import Path

import pandas as pd
from faker import Faker

from basicTestCase.basic_test_case import BasicTestCase

from app.CeleryTasks.post_processing_tests.post_processing_task import \
    PostProcessingBaseTask


class TestPostProcessingUseCase(BasicTestCase):

    def _setUp(self):
        self.uc = PostProcessingBaseTask()

        base_path = r"C:\Users\ammonk\OneDrive - Intel " \
                    r"Corporation\Desktop\Test_Folder\fake_uploads"
        self.data_path = base_path + r"\MentorHarbor_aux_to_main.csv"
        self.config_path = base_path + r"\userInput.xlsx"

    def test_init(self):
        uc = PostProcessingBaseTask()
        self.assertEqual(uc.test, None)

    def test_run_post_processing(self):
        with self.assertRaises(NotImplementedError):
            self.uc.run_post_processing(df=pd.DataFrame(), filter_by="dut")

    def test_format_response(self):
        fake_path = Path("This\Is\A\Fake\Path")
        result = self.uc.format_response(df_path=fake_path)

        '''
         expected result:

        d = {'current': 100,
             'total': 100,
             'status': 'None completed!',
             'result': "This\Is\A\Fake\Path",
             'filename': 'None_2020-09-11 10:34:59.174542'}
        '''

        self.assertIsInstance(result, dict)

        self.assertIn("filename", list(result.keys()))
        self.assertIn("status", list(result.keys()))
        self.assertIn("current", list(result.keys()))
        self.assertIn("total", list(result.keys()))
        self.assertIn("result", list(result.keys()))

        self.assertEqual(100, result["current"])
        self.assertEqual(100, result["total"])
        self.assertTrue("None_" in result["filename"])

        self.assertEqual(result['result'], "This\Is\A\Fake\Path")


    def test_format_filename(self):
        target = datetime.datetime(2020, 1, 1)
        with mock.patch.object(datetime, 'datetime', mock.Mock(
                wraps=datetime.datetime)) as patched:
            patched.now.return_value = target
            filename = self.uc.format_filename()

        self.assertEqual(f"None_{target}", filename)

    def test_extract_request_paths(self):
        f = Faker()
        test_name = f.name()
        data_filename = f.file_name(extension="csv")
        data_file_path = f.file_path(extension="csv")
        user_input_filename = f.file_name(extension="xlsx")
        user_input_path = f.file_path(extension="xlsx")

        input_dict = {"test_name": test_name,
                      "data_filename": data_filename,
                      "data_file_path": data_file_path,
                      "user_input_filename": user_input_filename,
                      "user_input_file_path": user_input_path,
                      "filter_by": "dut"}

        request = json.dumps(input_dict)

        expected_dict = input_dict

        expected_dict['data_path'] = expected_dict.pop("data_file_path")
        expected_dict['config_path'] = expected_dict.pop("user_input_file_path")
        expected_dict['config_filename'] = expected_dict.pop(
            "user_input_filename")

        result_dict = self.uc.extract_request_paths(request=request)

        for key, value in result_dict.items():
            self.assertEqual(expected_dict[key], value)

        for key, value in expected_dict.items():
            self.assertEqual(result_dict[key], value)

    def test_celery_update_state(self):

        x = self.uc.celery_update_state(state="STATE", current=10,
                                        total=100, status="CHECKING...")
        self.assertEqual(0, x)

    @mock.patch("app.CeleryTasks.post_processing_tests.post_processing_task."
                "PostProcessingBaseTask.data_prep_update_repository")
    @mock.patch("app.CeleryTasks.post_processing_tests.post_processing_task."
                "PostProcessingBaseTask.data_prep_clean")
    def test_data_preparation(self, mock_prep_clean, mock_update_repo):
        mock_update_path_str = "mock_update_path_str"
        mock_clean_path_str = "mock_clean_path_str"
        mock_update_repo.return_value = mock_update_path_str
        mock_prep_clean.return_value = mock_clean_path_str

        output_df_path_str = self.uc.data_preparation(data_path=self.data_path,
                                             config_path=self.config_path)

        mock_prep_clean.assert_called_once_with(data_path=self.data_path,
                                                config_path=self.config_path)
        mock_update_repo.assert_called_once_with(df_path_str=mock_clean_path_str)

        self.assertIsInstance(output_df_path_str, str)
        self.assertEqual(mock_update_path_str, output_df_path_str)
        #self.assertTrue(output_df.equals(pd.read_json(mock_json_df)))

    def test_data_prep_clean(self):

        df_pkl_path = self.uc.data_prep_clean(data_path=self.data_path,
                                          config_path=self.config_path)

        self.assertIsInstance(df_pkl_path, str)

        df = pd.read_pickle(df_pkl_path)
        self.assertIn("edge_rail", df)
        self.assertIn("associated_rail", df)
        self.assertIn("spec_max", df)
        self.assertIn("spec_min", df)
        self.assertIn("expected_nominal", df)
        self.assertIn("current_rail", df)
        self.assertIn("max_power", df)

    def test_data_prep_update_repository(self):
        # Nothing to really test here..
        pass

    '''
    def test_everything(self):
        self.fail(
            msg="Are you sure you want to run this? It may take awhile..."
        )
    '''

    def test_mismatched_data_and_input(self):
        base_path = r"C:\Users\ammonk\OneDrive - Intel " \
                    r"Corporation\Desktop\Test_Folder\fake_uploads\all_uploads\Aux To Main"
        data_path = base_path + r"\island_rapids_aux_to_main.csv"
        config_base_path = r"C:\Users\ammonk\OneDrive - Intel " \
                           r"Corporation\Desktop\Test_Folder\fake_uploads"
        config_path = config_base_path + r"\userInput.xlsx"

        input_dict = {"test_name": "Aux To Main",
                      "data_filename": "data_filename",
                      "data_file_path": data_path,
                      "user_input_filename": "user_input_filename",
                      "user_input_file_path": config_path,
                      "filter_by": "dut"}

        request = json.dumps(input_dict)

        expected_dict = input_dict

        with self.assertRaises(NotImplementedError):
            self.uc.run(request=request)

        #self.uc.data_preparation
        ## data_prep_clean
        ## data_prep_update_repository
        #self.uc.run_post_processing
        #self.uc.format_response()
