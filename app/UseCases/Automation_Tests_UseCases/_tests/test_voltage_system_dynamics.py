import typing as t
from pathlib import Path

import pandas as pd

from .test_automation_test_usecase import AutomationTestBaseCase

from app.UseCases.Automation_Tests_UseCases.automation_test_usecase import \
    AutomationTestRequestObject

from app.UseCases.Automation_Tests_UseCases.voltage_system_dynamics import \
    VoltageSystemDynamicsUseCase

from app.Repository.repository import Repository, MongoRepository


class TestVSDUseCase(AutomationTestBaseCase):
    uc = VoltageSystemDynamicsUseCase
    TEST = "voltage_system_dynamics"
    AUTOMATION_TEST = "Aux To Main"
    DEFAULT_FILTERBY = "testpoint"
    PLOT_FIELDS = ["Plot"]
    EXPECTED_SHEETS = ["VSD"]

    def _setUp(self):
        self.uc = VoltageSystemDynamicsUseCase(repo=MongoRepository())

    def test_product_path(self):
        self.build_processed_dataset()

    def test_island_rapids_default(self):
        product = "Island Rapids"
        filter_by = "default"
        self._test_product(product=product, filter_by=filter_by)

    def test_island_rapids_capture(self):
        product = "Island Rapids"
        filter_by = "capture"
        self._test_product(product=product, filter_by=filter_by)

    def test_island_rapids_runid(self):
        product = "Island Rapids"
        filter_by = "runid"
        self._test_product(product=product, filter_by=filter_by)

    def test_island_rapids_sample(self):
        product = "Island Rapids"
        filter_by = "sample"
        self._test_product(product=product, filter_by=filter_by)

    def test_island_rapids_rework(self):
        product = "Island Rapids"
        filter_by = "rework"
        self._test_product(product=product, filter_by=filter_by)

    def test_island_rapids_pba(self):
        product = "Island Rapids"
        filter_by = "pba"
        self._test_product(product=product, filter_by=filter_by)

    def test_island_rapids_dut(self):
        product = "Island Rapids"
        filter_by = "dut"
        self._test_product(product=product, filter_by=filter_by)