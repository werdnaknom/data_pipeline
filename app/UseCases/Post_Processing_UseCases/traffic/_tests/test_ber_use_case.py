from unittest import TestCase, mock
from collections import OrderedDict
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
from app.shared.Entities.entities import EthAgentCaptureEntity

from app.UseCases.Post_Processing_UseCases.traffic.check_crc_errors_use_case \
    import PortConfidenceLevelResult, PortErrorResult, BERGroupResult, \
    PostProcessingUseCase, PostProcessingRequestObject, TrafficProcessingUseCase


class TestSequencingUseCase(BasicTestCase):
    logger_name = 'Waveform Sequencing Test'

    def _load_traffic_pp_df(self) -> pd.DataFrame:
        # df = pd.read_pickle(r"C:\Users\ammonk\OneDrive - Intel "
        #                    r"Corporation\Desktop\Test_Folder\fake_uploads
        #                    \CeleryTemp\WaveformUpdateMongo_QSPcuAxKBYRUmEwWsItp.pkl")

        df = pd.read_csv(r"C:\Users\ammonk\OneDrive - Intel "
                         r"Corporation\Desktop\Test_Folder\fake_uploads\mentor_harbor_pp_ethagent.csv")
        return df

    def _setUp(self):
        self.mock_repo = mock.MagicMock(Repository)
        self.uc = TrafficProcessingUseCase(repo=self.mock_repo)
        self.test_df = self._load_traffic_pp_df()
        products = self.test_df.product_id.unique()
        pbas = self.test_df.pba_id.unique()
        reworks = self.test_df.rework_id.unique()
        submissions = self.test_df.submission_id.unique()
        runids = self.test_df.run_id.unique()
        tests = self.test_df.automation_id.unique()
        captures = self.test_df.datacapture_id.unique()
        self.fake_projects = [entity.to_dict() for entity in
                              self.create_fake_product_entities(len(products))]
        for i, product in enumerate(self.fake_projects):
            product["_id"] = products[i]
        self.fake_pbas = [entity.to_dict() for entity in
                          self.create_fake_pba_entities(len(pbas))]
        for i, pba in enumerate(self.fake_pbas):
            pba["_id"] = pbas[i]
        self.fake_reworks = [entity.to_dict() for entity in
                             self.create_fake_rework_entities(len(reworks))]
        for i, rework in enumerate(self.fake_reworks):
            rework["_id"] = reworks[i]
        self.fake_submissions = [entity.to_dict() for entity in
                                 self.create_fake_submission_entities(
                                     len(submissions))]
        for i, sub in enumerate(self.fake_submissions):
            sub["_id"] = submissions[i]
        self.fake_runids = [entity.to_dict() for entity in
                            self.create_fake_runid_entities(len(runids))]
        for i, runid in enumerate(self.fake_runids):
            runid["_id"] = runids[i]
        self.fake_tests = [entity.to_dict() for entity in
                           self.create_fake_automation_test_entities(len(
                               tests))]
        for i, test in enumerate(self.fake_tests):
            test["_id"] = tests[i]
        self.fake_traffic_captures = [entity.to_dict() for entity in
                                      self.create_fake_traffic_capture_entities(
                                          len(captures))]
        for i, capture in enumerate(self.fake_traffic_captures):
            capture["_id"] = captures[i]

    def test_process_request(self):
        self.mock_repo.query_projects.return_value = self.fake_projects
        self.mock_repo.query_pbas.return_value = self.fake_pbas
        self.mock_repo.query_reworks.return_value = self.fake_reworks
        self.mock_repo.query_submissions.return_value = self.fake_submissions
        self.mock_repo.query_runids.return_value = self.fake_runids
        self.mock_repo.query_automation_tests.return_value = self.fake_tests
        self.mock_repo.query_traffic_captures.return_value = self.fake_traffic_captures
        req = PostProcessingRequestObject(filters=[],
                                          df=self.test_df)

        uc = TrafficProcessingUseCase(repo=MongoRepository())
        resp = uc.execute(request_object=req)

        self.assertTrue(resp)
        od = resp.value
        self.assertIsInstance(od, tuple)
        self.assertIsInstance(od[0], str)
        self.assertIsInstance(od[1], pd.DataFrame)
        self.assertEqual(od[0], "BitErrorRatio")
