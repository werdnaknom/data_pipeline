import typing as t
from pathlib import Path

import pandas as pd

from .test_automation_test_usecase import AutomationTestBaseCase

from app.UseCases.Automation_Tests_UseCases.automation_test_usecase import \
    AutomationTestRequestObject

from app.UseCases.Automation_Tests_UseCases.load_profile import \
    LoadProfileUseCase

from app.Repository.repository import Repository, MongoRepository


class TestLoadProfileUseCase(AutomationTestBaseCase):
    TEST = "load_profile"
    AUTOMATION_TEST = "Load Profile"
    DEFAULT_FILTERBY = "capture"
    PLOT_FIELDS = ["Plot"]
    EXPECTED_SHEETS = ["Power&Current", "Load Profile"]

    def _setUp(self):
        self.uc = LoadProfileUseCase(repo=MongoRepository())

    def test_mentor_harbor_default(self):
        product = "Mentor Harbor"
        filter_by = "default"
        self._test_product(product=product, filter_by=filter_by)

    def test_mentor_harbor_capture(self):
        product = "Mentor Harbor"
        filter_by = "capture"
        self._test_product(product=product, filter_by=filter_by)

    def test_mentor_harbor_runid(self):
        product = "Mentor Harbor"
        filter_by = "runid"
        self._test_product(product=product, filter_by=filter_by)

    def test_mentor_harbor_sample(self):
        product = "Mentor Harbor"
        filter_by = "sample"
        self._test_product(product=product, filter_by=filter_by)

    def test_mentor_harbor_rework(self):
        product = "Mentor Harbor"
        filter_by = "rework"
        self._test_product(product=product, filter_by=filter_by)

    def test_mentor_harbor_pba(self):
        product = "Mentor Harbor"
        filter_by = "pba"
        self._test_product(product=product, filter_by=filter_by)

    def test_mentor_harbor_dut(self):
        product = "Mentor Harbor"
        filter_by = "dut"
        self._test_product(product=product, filter_by=filter_by)

