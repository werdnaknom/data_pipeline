import typing as t
from pathlib import Path

import pandas as pd

from app.UseCases.Automation_Test_Post_Processing._tests \
    .IFailedAtOnePointBaseCase import IFailedAtOncePointBaseCase

from app.UseCases.Automation_Tests_UseCases.automation_test_usecase import \
    AutomationTestRequestObject

# from app.UseCases.Automation_Tests_UseCases.load_profile import \
#    LoadProfileUseCase
from app.UseCases.Automation_Tests_UseCases.sequencing import SequencingUseCase
from app.UseCases.Automation_Tests_UseCases.voltage_system_dynamics import \
    VoltageSystemDynamicsUseCase

from app.Repository.repository import Repository, MongoRepository


class AuxToMainToLoadProfileOnIslandRapids(IFailedAtOncePointBaseCase):
    '''
    This data was created by Alex and failed with the error:
        list index out of range
        Result: FAILURE
    '''
    BASE_DIRECTORY = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's Code\unit_test_data\IFailedAtOnePoint\IslandRapids_Sequencing_NoneType_Float_Compare"
    AUTOMATION_TEST_DATAFOLDER = "Sequencing"
    DEFAULT_FILTERBY = "capture"
    PLOT_FIELDS = ["Plot"]
    EXPECTED_SHEETS = ["Sequencing"]

    def _setUp(self):
        self.uc = SequencingUseCase(repo=MongoRepository())

    def test_dut_filter(self):
        self._test_filter(filter_by="dut")
