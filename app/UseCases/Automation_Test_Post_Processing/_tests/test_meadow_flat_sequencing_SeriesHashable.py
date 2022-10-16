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
    This data was created by Azmin and failed with the error:
        "'Series' objects are mutable, thus they cannot be hashed
         Result: FAILURE".
           The error was caused by duplicating the DF due to slew rate considerations.
    '''
    BASE_DIRECTORY = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's Code\unit_test_data\IFailedAtOnePoint\Meadow_Sequencing_SeriesHashable"
    AUTOMATION_TEST_DATAFOLDER = "Sequencing"
    DEFAULT_FILTERBY = "capture"
    PLOT_FIELDS = []
    EXPECTED_SHEETS = ["Sequencing", "Power-On Time"]

    def _setUp(self):
        self.uc = SequencingUseCase(repo=MongoRepository())

    def test_dut_filter(self):
        self._test_filter(filter_by="dut")
