import typing as t
from pathlib import Path

import pandas as pd

from app.UseCases.Automation_Test_Post_Processing._tests \
    .IFailedAtOnePointBaseCase import IFailedAtOncePointBaseCase

from app.UseCases.Automation_Tests_UseCases.automation_test_usecase import \
    AutomationTestRequestObject

from app.UseCases.Automation_Tests_UseCases.inrush import InrushUseCase

from app.Repository.repository import Repository, MongoRepository


class AuxToMainToInrushOnFoxPond(IFailedAtOncePointBaseCase):
    '''
    '''
    BASE_DIRECTORY = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's Code\unit_test_data\IFailedAtOnePoint\FoxPond_All_Data_Inrush"
    AUTOMATION_TEST_DATAFOLDER = "Inrush"
    DEFAULT_FILTERBY = "capture"
    PLOT_FIELDS = ["Plot"]
    EXPECTED_SHEETS = ["Inrush"]

    def _setUp(self):
        self.uc = InrushUseCase(repo=MongoRepository())

    def test_dut_filter(self):
        with self.assertRaises(ValueError):
            self._test_filter(filter_by="runid")
