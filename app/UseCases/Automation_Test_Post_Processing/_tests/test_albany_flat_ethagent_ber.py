import typing as t
from pathlib import Path

import pandas as pd

from app.UseCases.Automation_Test_Post_Processing._tests \
    .IFailedAtOnePointBaseCase import IFailedAtOncePointBaseCase

from app.UseCases.Automation_Tests_UseCases.automation_test_usecase import \
    AutomationTestRequestObject

from app.UseCases.Automation_Tests_UseCases.ber import BitErrorRatioUseCase

from app.Repository.repository import Repository, MongoRepository


class EthAgentBitErrorRatioAlbanyFlatKulim(IFailedAtOncePointBaseCase):
    '''
    This data was created by Azmin and failed with the error:
        list index out of range
        Result: FAILURE

    The DATACSV was incorrect in this case.  In a couple of the rows in
    DATACSV, the test_category field was a data path instead of "EthAgent"
    '''
    BASE_DIRECTORY = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's Code\unit_test_data\IFailedAtOnePoint\AlbanyFlat_EthAgent_BER"
    AUTOMATION_TEST_DATAFOLDER = "EthAgent"
    DEFAULT_FILTERBY = "datacapture"
    PLOT_FIELDS = ["Plot"]
    EXPECTED_SHEETS = ["BER"]

    def _setUp(self):
        self.uc = BitErrorRatioUseCase(repo=MongoRepository())

    def test_dut_filter(self):
        with self.assertRaises(AttributeError):
            self._test_filter(filter_by="dut")
