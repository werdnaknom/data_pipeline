import typing as t
from pathlib import Path

import pandas as pd

from .test_automation_test_usecase import AutomationTestBaseCase

from app.UseCases.Automation_Tests_UseCases.automation_test_usecase import \
    AutomationTestRequestObject

from app.UseCases.Automation_Tests_UseCases.sequencing import SequencingUseCase

from app.Repository.repository import Repository, MongoRepository


class TestSequencingUseCase(AutomationTestBaseCase):
    TEST = "sequencing"
    AUTOMATION_TEST = "Aux To Main"
    DEFAULT_FILTERBY = "capture"
    PLOT_FIELDS = []
    EXPECTED_SHEETS = ["Sequencing", "Power-On Time"]

    def _setUp(self):
        self.uc = SequencingUseCase(repo=MongoRepository())

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

    def test_fox_pond_dut(self):
        product = "Fox Pond"
        filter_by = "dut"
        self._test_product(product=product, filter_by=filter_by)

    def test_fox_pond_pba(self):
        product = "Fox Pond"
        filter_by = "pba"
        self._test_product(product=product, filter_by=filter_by)

    def test_fox_pond_runid(self):
        product = "Fox Pond"
        filter_by = "runid"
        self._test_product(product=product, filter_by=filter_by)

    def test_dataframe_filtering(self):
        req = self._AutomationTest_request_object(product="Island Rapids",
                                                  filter_by="dut")
        df = req.df
        print(df.shape)
