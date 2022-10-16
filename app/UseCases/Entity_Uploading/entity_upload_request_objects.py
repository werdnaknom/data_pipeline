import typing as t

import pandas as pd

from app.shared.Requests.requests import ValidRequestObject
from app.shared.Entities.file_entities import CaptureEnvironmentFileEntity, \
    ProbesFileEntity, StatusFileEntity, CommentsFileEntity, \
    SystemInfoFileEntity, TestRunFileEntity, CaptureSettingsEntity, \
    LPTrafficFileEntity, DUTTrafficFileEntity


class EntityIDRequestObject(ValidRequestObject):

    @classmethod
    def extract_project_name(cls, row: pd.Series) -> str:
        return row['dut']

    @classmethod
    def extract_pba(cls, row: pd.Series) -> str:
        return row['pba']

    @classmethod
    def extract_rework(cls, row: pd.Series) -> int:
        return int(row['rework'])

    @classmethod
    def extract_submission(cls, row: pd.Series) -> str:
        return row['serial_number']

    @classmethod
    def extract_runid(cls, row: pd.Series) -> int:
        return int(row['runid'])

    @classmethod
    def extract_automation_test(cls, row: pd.Series) -> str:
        return row['test_category']

    @classmethod
    def extract_datacapture(cls, row: pd.Series) -> int:
        return int(row['capture'])


'''

PROJECT ID

'''


class ProjectIDRequestObject(EntityIDRequestObject):
    project_name: str
    silicon: list = []

    def __init__(self, row: pd.Series):
        self.project_name = self.extract_project_name(row)


'''

PBA ID

'''


class PBAIDRequestObject(EntityIDRequestObject):
    project_name: str
    part_number: str
    notes: str
    reworks: list
    customers: list

    def __init__(self, row: pd.Series, notes: str = "", reworks: list = None,
                 customers: list = None):
        if reworks is None:
            reworks = list()
        if customers is None:
            customers = list()
        self.project_name = self.extract_project_name(row)
        self.part_number = self.extract_pba(row)
        self.notes = notes
        self.reworks = reworks
        self.customers = customers


'''

REWORK 

'''


class ReworkIDRequestObject(EntityIDRequestObject):
    part_number: str
    rework: int
    notes: str
    rework: int
    eetrack_id: str

    def __init__(self, row: pd.Series, notes: str = "", eetrack_id: str = ""):
        self.part_number = self.extract_pba(row)
        self.rework = self.extract_rework(row)
        self.eetrack_id = eetrack_id
        self.notes = notes


'''

Submission 

'''


class SubmissionIDRequestObject(EntityIDRequestObject):
    submission: str
    rework: int
    part_number: str

    def __init__(self, row: pd.Series):
        self.part_number = self.extract_pba(row)
        self.rework = self.extract_rework(row)
        self.submission = self.extract_submission(row)


'''

Runid 

'''


class RunIDRequestObject(EntityIDRequestObject):
    runid: int
    status: StatusFileEntity
    comments: CommentsFileEntity
    system_info: SystemInfoFileEntity
    testrun: TestRunFileEntity

    def __init__(self, row: pd.Series):
        self.runid = self.extract_runid(row)
        self.status = StatusFileEntity.from_dataframe_row(df_row=row)
        self.comments = CommentsFileEntity.from_dataframe_row(df_row=row)
        self.system_info = SystemInfoFileEntity.from_dataframe_row(df_row=row)
        self.testrun = TestRunFileEntity.from_dataframe_row(df_row=row)


'''

    AUTOMATION TEST_NAME

'''


class AutomationTestRequestObject(EntityIDRequestObject):
    test_name: str
    notes: str

    def __init__(self, row: pd.Series, notes: str = ""):
        self.test_name = self.extract_automation_test(row)
        self.notes = notes


'''

    DATACAPTURE

'''


class DataCaptureRequestObject(EntityIDRequestObject):
    capture: int
    runid: int
    test_category: str
    environment_configuration: CaptureEnvironmentFileEntity

    def __init__(self, row: pd.Series):
        self.capture = self.extract_datacapture(row)
        self.runid = self.extract_runid(row)
        self.test_category = self.extract_automation_test(row)
        self.environment_configuration = \
            CaptureEnvironmentFileEntity.from_dataframe_row(row)


class WaveformCaptureRequestObject(DataCaptureRequestObject):
    settings: CaptureSettingsEntity

    def __init__(self, row: pd.Series):
        super(WaveformCaptureRequestObject, self).__init__(row=row)
        self.settings = \
            CaptureSettingsEntity.from_dataframe_row(df_row=row)


class EthAgentCaptureRequestObject(DataCaptureRequestObject):
    dut: DUTTrafficFileEntity
    lp: LPTrafficFileEntity

    def __init__(self, row: pd.Series):
        super(EthAgentCaptureRequestObject, self).__init__(row=row)
        self.dut = DUTTrafficFileEntity.from_dataframe_row(df_row=row)
        self.lp = LPTrafficFileEntity.from_dataframe_row(df_row=row)
