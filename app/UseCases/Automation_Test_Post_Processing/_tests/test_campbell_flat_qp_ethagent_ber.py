import typing as t
from pathlib import Path

import pandas as pd

from app.UseCases.Automation_Test_Post_Processing._tests \
    .IFailedAtOnePointBaseCase import IFailedAtOncePointBaseCase

from app.UseCases.Automation_Tests_UseCases.automation_test_usecase import \
    AutomationTestRequestObject

from app.UseCases.Automation_Tests_UseCases.ber import BitErrorRatioUseCase

from app.Repository.repository import Repository, MongoRepository


class EthAgentBitErrorRatioCampbellFlatQPKulim(IFailedAtOncePointBaseCase):
    '''
    This data was created by Azmin and failed with the error:
        Cannot encode object: 0, of type: <class numpy.int64>

    This failure was caused by the MAC being 0.  Fixed by forcing the
    datatype of MAC to a string.

    '''
    BASE_DIRECTORY = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's Code\unit_test_data\IFailedAtOnePoint\CampbellFlat_QP_EthAgent_BER"
    AUTOMATION_TEST_DATAFOLDER = "EthAgent"
    DEFAULT_FILTERBY = "datacapture"
    PLOT_FIELDS = []
    EXPECTED_SHEETS = ["BitErrorRatio"]

    def _setUp(self):
        self.uc = BitErrorRatioUseCase(repo=MongoRepository())

    def test_dut_filter(self):
        self._test_filter(filter_by="dut")
