from unittest import TestCase, mock
import logging
import sys
import numpy as np

import mongomock

import pandas as pd
from app.shared.Responses.response import ResponseSuccess

from app.Repository.repository import Repository

from basicTestCase.basic_test_case import BasicTestCase

from app.UseCases.Entity_Uploading.csv_to_repo_usecase import \
    CSVToRepositoryUseCase, CSVToRepoRequestObject


class TakeCSVToRepository(BasicTestCase):
    logger_name = "CSVtoRepoTestCase"

    def test_process_request(self):
        mock_repo = mock.MagicMock(Repository)

        mock_repo.find_project_id.return_value = None
        mock_repo.find_pba_id.return_value = None
        mock_repo.find_rework_id.return_value = None
        mock_repo.find_submission_id.return_value = None
        mock_repo.find_run_id.return_value = None
        mock_repo.find_automation_test_id.return_value = None
        mock_repo.find_waveform_capture_id.return_value = None
        mock_repo.find_waveform_id.return_value = None
        mock_repo.insert_waveform.return_value = "wf1234"
        mock_repo.insert_one.return_value = "123456"

        input_df = self._helper_load_capture_df()
        df_json = input_df.to_json()

        req = CSVToRepoRequestObject(df_json=df_json)
        uc = CSVToRepositoryUseCase(repo=mock_repo)
        resp = uc.process_request(request_object=req)

        self.assertTrue(resp)

        df = resp.value
        self.assertIsInstance(df, pd.DataFrame)

        project_expected = input_df.iloc[0].dut
        pba_expected = input_df.iloc[0].pba
        rework_expected = int(input_df.iloc[0].rework)
        submission_expected = input_df.iloc[0].serial_number
        runid_expected = int(input_df.iloc[0].runid)
        automation_expected = input_df.iloc[0].test_category
        capture_expected = int(input_df.iloc[0].capture)
        testpoints_expected = list(input_df.testpoint)

        self.assertTrue(uc.COLUMN_PRODUCT_ID in df.columns)
        self.assertEqual(df[uc.COLUMN_PRODUCT_ID].unique(), ["123456"])
        mock_repo.find_project_id.assert_called_once_with(
            project_name=project_expected)

        self.assertTrue(uc.COLUMN_PBA_ID in df.columns)
        self.assertEqual(df[uc.COLUMN_PBA_ID].unique(), ["123456"])
        mock_repo.find_pba_id.assert_called_once_with(
            part_number=pba_expected,
            project=project_expected)

        self.assertTrue(uc.COLUMN_REWORK_ID in df.columns)
        self.assertEqual(df[uc.COLUMN_REWORK_ID].unique(), ["123456"])
        mock_repo.find_rework_id.assert_called_once_with(
            rework_number=rework_expected,
            pba=pba_expected)

        self.assertTrue(uc.COLUMN_SUBMISSION_ID in df.columns)
        self.assertEqual(df[uc.COLUMN_SUBMISSION_ID].unique(), ["123456"])
        mock_repo.find_submission_id.assert_called_once_with(
            submission=submission_expected,
            pba=pba_expected,
            rework=rework_expected
        )

        self.assertTrue(uc.COLUMN_RUN_ID in df.columns)
        self.assertEqual(df[uc.COLUMN_RUN_ID].unique(), ["123456"])
        mock_repo.find_run_id.assert_called_once_with(
            runid=runid_expected
        )

        self.assertTrue(uc.COLUMN_AUTOMATION_ID in df.columns)
        self.assertEqual(df[uc.COLUMN_AUTOMATION_ID].unique(), ["123456"])
        mock_repo.find_automation_test_id.assert_called_once_with(
            test_name=automation_expected
        )

        self.assertTrue(uc.COLUMN_DATACAPTURE_ID in df.columns)
        self.assertEqual(df[uc.COLUMN_DATACAPTURE_ID].unique(), ["123456"])
        mock_repo.find_waveform_capture_id.assert_called_once_with(
            capture=capture_expected,
            runid=runid_expected,
            test=automation_expected
        )

        self.assertTrue(uc.COLUMN_WAVEFORM_ID in df.columns)
        self.assertEqual(df[uc.COLUMN_WAVEFORM_ID].unique(), ["wf1234"])
        calls = [
            mock.call(
                testpoint=testpoint,
                capture=capture_expected,
                runid=runid_expected,
                test_category=automation_expected,
                scope_channel=i + 1
            ) for i, testpoint in enumerate(testpoints_expected)
        ]
        mock_repo.find_waveform_id.assert_has_calls(calls=[
            mock.call(
                testpoint=testpoint,
                capture=capture_expected,
                runid=runid_expected,
                test_category=automation_expected,
                scope_channel=i + 1
            ) for i, testpoint in enumerate(testpoints_expected)]
        )
