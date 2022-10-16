from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, asdict, field
import typing as t
from bson import ObjectId
import datetime

import numpy as np

from app.shared.Helpers.waveform_functions import find_steady_state_wf
from app.shared.Helpers.path_translator import PathTranslator

from app.shared.Entities import Entity, _EntityBase

from app.shared.Entities.file_entities import CommentsFileEntity, \
    StatusFileEntity, SystemInfoFileEntity, TestRunFileEntity, \
    CaptureEnvironmentFileEntity, ProbesFileEntity, CaptureSettingsEntity, \
    LPTrafficFileEntity, DUTTrafficFileEntity

IDTYPE = t.Optional[str]
TriStateType = t.TypeVar('TriStateType', bool, type(None))

LIST_OF_SILICON = t.List[str]
PROJECT_DESCRIPTOR = str


@dataclass(init=False)
class Tristate:
    value: TriStateType

    def __init__(self, value=None):
        if any(value is v for v in (True, False, None)):
            self.value = value
        else:
            raise ValueError("Tristate value must be True, False, or None")

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, adict: dict):
        return cls(**adict)


@dataclass
class _SiliconBase:
    name: str
    acronym: str
    features: dict
    _type: str = "SILICON"


@dataclass()
class SiliconEntity(_EntityBase, _SiliconBase, Entity):

    def __post_init__(self):
        if self._id is None:
            self._id = self.format_id(silicon_name=self.name)

    @property
    def descriptor(self) -> str:
        return self.name

    @classmethod
    def format_id(cls, silicon_name: str):
        return silicon_name

    def get_filter(self) -> dict:
        return {"name": self.name}

    @classmethod
    def search_filter(cls, name: str) -> dict:
        return {"name": name}

    def to_result(self) -> OrderedDict:
        return OrderedDict([('Silicon', self.acronym)])


@dataclass
class _ProjectBase:
    name: str
    silicon: LIST_OF_SILICON = field(default_factory=list)
    _type: str = "PROJECT"


@dataclass()
class ProjectEntity(_EntityBase, _ProjectBase, Entity):
    ''' Projects _ID should be it's Name'''

    @property
    def descriptor(self) -> str:
        return self.name

    def __post_init__(self):
        if self._id is None:
            self._id = self.format_id(project_name=self.name)

    @classmethod
    def format_id(cls, project_name) -> str:
        return cls.format_without_spaces(word=project_name).lower()

    @classmethod
    def from_dataframe_row(cls, df_row) -> ProjectEntity:
        proj = ProjectEntity(name=df_row.dut)
        return proj

    def get_filter(self) -> dict:
        return {"name": self.name}

    @classmethod
    def search_filter(cls, name: str) -> dict:
        return {"name": name}

    def to_result(self) -> OrderedDict:
        return OrderedDict([('DUT', self.name)])


@dataclass
class _ReworkBase:
    pba: str
    rework: int
    notes: str = ""
    eetrack_id: str = ""
    _type: str = "REWORK"
    ID_FMT: str = "{pba}_REWORK_{rework}"


@dataclass()
class ReworkEntity(_EntityBase, _ReworkBase, Entity):

    def __post_init__(self):
        self.rework = int(self.rework)
        if self._id is None:
            self._id = self.format_id(pba=self.pba,
                                      rework=self.rework)

    @property
    def descriptor(self) -> str:
        return str(self.rework)

    @classmethod
    def format_id(cls, pba: str, rework: int) -> str:
        return cls.ID_FMT.format(pba=pba, rework=rework)

    @classmethod
    def from_dataframe_row(cls, df_row) -> ReworkEntity:
        rework = ReworkEntity(rework=df_row.rework,
                              pba=df_row.pba,
                              eetrack_id=df_row.software
                              )
        return rework

    def get_filter(self) -> dict:
        return {"rework": self.rework,
                "pba": self.pba}

    @classmethod
    def search_filter(cls, rework: int, pba: str) -> dict:
        return {"rework": int(rework),
                "pba": pba}

    def to_result(self) -> OrderedDict:
        return OrderedDict([('Rework', self.rework)])


@dataclass
class _PBABase:
    part_number: str
    project: str
    notes: str = ""
    reworks: t.List[str] = field(default_factory=list)
    customers: t.List[str] = field(default_factory=list)
    _type: str = "PBA"


@dataclass()
class PBAEntity(_EntityBase, _PBABase, Entity):
    ''' PBA's _ID is it's part_number '''

    def __post_init__(self):
        if self._id is None:
            self._id = self.format_id(part_number=self.part_number)

    @property
    def descriptor(self) -> str:
        return self.part_number

    @classmethod
    def format_id(cls, part_number) -> str:
        return part_number

    @classmethod
    def from_dataframe_row(cls, df_row) -> PBAEntity:
        pba = cls(part_number=df_row['pba'],
                  project=df_row['dut'])
        return pba

    def add_rework(self, rework: ObjectId):
        self.reworks.append(rework)

    def add_customer(self, customer: str):
        self.customers.append(customer)

    def get_filter(self) -> dict:
        return {"part_number": self.part_number,
                "project": self.project}

    @classmethod
    def search_filter(cls, part_number: str, project: str) -> dict:
        return {"part_number": part_number,
                "project": project}

    def to_result(self) -> OrderedDict:
        return OrderedDict([("PBA", self.part_number)])


@dataclass
class _SubmissionBase:
    submission: str
    rework: int
    pba: str
    ID_FMT: str = "{submission}_{pba}_{rework}"
    _type: str = "SUBMISSION"


@dataclass()
class SubmissionEntity(_EntityBase, _SubmissionBase, Entity):

    def __post_init__(self):
        self.rework = int(self.rework)
        if self._id is None:
            self._id = self.format_id(submission=self.submission,
                                      pba=self.pba,
                                      rework=self.rework)

    @property
    def descriptor(self) -> str:
        return self.submission

    @classmethod
    def format_id(cls, submission: str, pba: str, rework: int) -> str:
        return cls.ID_FMT.format(submission=submission, pba=pba, rework=rework)

    @classmethod
    def from_dataframe_row(cls, df_row) -> SubmissionEntity:
        sub = SubmissionEntity(submission=df_row.serial_number,
                               rework=df_row.rework,
                               pba=df_row.pba)
        return sub

    def get_filter(self) -> dict:
        return {"submission": self.submission,
                "rework": self.rework,
                "pba": self.pba}

    @classmethod
    def search_filter(cls, submission: str, rework: int, pba: str) -> dict:
        return {"submission": submission,
                "rework": rework,
                "pba": pba}

    def to_result(self) -> OrderedDict:
        return OrderedDict([('DUT Serial', self.descriptor)])


@dataclass
class _RunidBase:
    runid: int
    status: StatusFileEntity
    system_info: SystemInfoFileEntity
    testrun: TestRunFileEntity
    comments: CommentsFileEntity
    _type: str = "RUNID"


@dataclass()
class RunidEntity(_EntityBase, _RunidBase, Entity):
    '''

    '''

    def __post_init__(self):
        self.runid = int(self.runid)
        if self._id is None:
            self._id = self.format_id(runid=self.runid)

    @property
    def descriptor(self) -> str:
        return str(self.runid)

    @classmethod
    def format_id(cls, runid) -> str:
        return str(runid)

    @classmethod
    def from_dataframe_row(cls, df_row) -> RunidEntity:
        comments = CommentsFileEntity.from_dataframe_row(df_row=df_row)
        testrun = TestRunFileEntity.from_dataframe_row(df_row=df_row)
        status = StatusFileEntity.from_dataframe_row(df_row=df_row)
        system = SystemInfoFileEntity.from_dataframe_row(df_row=df_row)

        runid = RunidEntity(runid=df_row.runid,
                            comments=comments,
                            testrun=testrun,
                            status=status,
                            system_info=system)

        return runid

    @classmethod
    def from_dict(cls, adict: dict) -> RunidEntity:
        comments = CommentsFileEntity.from_dict(adict=adict.pop("comments"))
        testrun = TestRunFileEntity.from_dict(adict=adict.pop("testrun"))
        status = StatusFileEntity.from_dict(adict=adict.pop("status"))
        system = SystemInfoFileEntity.from_dict(adict=adict.pop("system_info"))

        runid = RunidEntity(runid=adict['runid'],
                            comments=comments,
                            testrun=testrun,
                            status=status,
                            system_info=system)
        return runid

    def get_filter(self) -> dict:
        return {"runid": self.runid}

    @classmethod
    def search_filter(cls, runid: int) -> dict:
        return {"runid": int(runid)}

    def to_result(self) -> OrderedDict:
        result_dict = OrderedDict([("Runid", self.runid)])

        comments = self.comments.to_result()
        result_dict.update(comments)

        status = self.status.to_result()
        result_dict.update(status)

        testrun = self.testrun.to_result()
        result_dict.update(testrun)

        return result_dict


@dataclass
class _TestBase:
    name: str
    notes: str = ""
    _type: str = "AUTOMATIONTEST"


@dataclass()
class AutomationTestEntity(_EntityBase, _TestBase, Entity):
    '''

    '''

    def __post_init__(self):
        #TODO:: Update NAME LIST
        '''
        name_list = ["Aux To Main", "EthAgent", "Load Profile", "Scripts",
                     "Ripple"]
        if self.name not in name_list:
            raise AttributeError(f"Automation Test is {self.name}, which is "
                                 f"not in the standard list. Is this correct?"
                                 f" Expected name list:{name_list}")
        '''
        if self._id is None:
            self._id = self.format_id(test_name=self.name)

    @property
    def descriptor(self) -> str:
        return self.name

    @classmethod
    def format_id(cls, test_name: str) -> str:
        return cls.format_test_category(word=test_name)

    @classmethod
    def from_dataframe_row(cls, df_row) -> AutomationTestEntity:
        at = AutomationTestEntity(name=df_row.test_category)
        return at

    def get_filter(self) -> dict:
        return {"_id": self._id}

    @classmethod
    def search_filter(cls, name: str) -> dict:
        return {"name": name}

    def to_result(self) -> OrderedDict:
        return OrderedDict([("Automation Test", self.name)])


@dataclass
class _WaveformCaptureBase:
    capture: int
    runid: int
    test_category: str
    capture_settings: CaptureSettingsEntity
    environment: CaptureEnvironmentFileEntity
    ID_FMT: str = "waveform_{runid}_{test}_{capture}"
    _type: str = "DATACAPTURE"


@dataclass()
class WaveformCaptureEntity(_EntityBase, _WaveformCaptureBase, Entity):

    def __post_init__(self):
        self.runid = int(self.runid)
        self.capture = int(self.capture)
        if self._id is None:
            self._id = self.format_id(runid=self.runid,
                                      test_category=self.test_category,
                                      capture=self.capture)

    @property
    def descriptor(self) -> str:
        return str(self.capture)

    @classmethod
    def format_id(cls, runid: int, test_category: str, capture: int) -> str:
        test_category = cls.format_test_category(word=test_category)
        return cls.ID_FMT.format(runid=runid, test=test_category,
                                 capture=capture)

    @classmethod
    def from_dataframe_row(cls, df_row) -> WaveformCaptureEntity:
        settings = CaptureSettingsEntity.from_dataframe_row(df_row=df_row)
        environment = CaptureEnvironmentFileEntity.from_dataframe_row(
            df_row=df_row)
        capture = WaveformCaptureEntity(capture=df_row.capture,
                                        runid=df_row.runid,
                                        test_category=df_row.test_category,
                                        capture_settings=settings,
                                        environment=environment,
                                        )
        return capture

    @classmethod
    def from_dict(cls, adict: dict) -> WaveformCaptureEntity:
        settings = CaptureSettingsEntity.from_dict(adict=adict.pop(
            "capture_settings"))
        environment = CaptureEnvironmentFileEntity.from_dict(
            adict=adict.pop("environment"))
        capture = WaveformCaptureEntity(capture=adict["capture"],
                                        runid=adict["runid"],
                                        test_category=adict["test_category"],
                                        capture_settings=settings,
                                        environment=environment,
                                        )
        return capture

    def get_filter(self) -> dict:
        return {"capture": self.capture,
                "runid": self.runid,
                "test_category": self.test_category}

    @classmethod
    def search_filter(cls, capture: int, runid: int,
                      test_category: str) -> dict:
        search_dict = {}

        if test_category is not None:
            search_dict["test_category"] = test_category
        if capture is not None:
            search_dict['capture'] = int(capture)
        if runid is not None:
            search_dict['runid'] = int(runid)

        return search_dict

    def to_result(self) -> OrderedDict:
        environment = self.environment.to_result()
        result_dict = OrderedDict([("Capture", self.capture)])
        result_dict.update(environment)
        return result_dict


@dataclass
class _EthAgentCaptureBase:
    capture: int
    runid: int
    test_category: str
    environment: CaptureEnvironmentFileEntity
    lp: LPTrafficFileEntity
    dut: DUTTrafficFileEntity
    ID_FMT: str = "ethagent_{runid}_{test}_{capture}"
    _type: str = "DATACAPTURE"


@dataclass()
class EthAgentCaptureEntity(_EntityBase, _EthAgentCaptureBase, Entity):

    def __post_init__(self):
        self.runid = int(self.runid)
        self.capture = int(self.capture)
        if self._id is None:
            self._id = self.format_id(runid=self.runid,
                                      test_category=self.test_category,
                                      capture=self.capture)

    @property
    def descriptor(self) -> str:
        return str(self.capture)

    @classmethod
    def format_id(cls, runid: int, test_category: str, capture: int) -> str:
        test_category = cls.format_test_category(word=test_category)
        return cls.ID_FMT.format(runid=runid, test=test_category,
                                 capture=capture)

    @classmethod
    def from_dataframe_row(cls, df_row) -> EthAgentCaptureEntity:
        environment = CaptureEnvironmentFileEntity.from_dataframe_row(
            df_row=df_row)
        dut = DUTTrafficFileEntity.from_dataframe_row(df_row=df_row)
        lp = LPTrafficFileEntity.from_dataframe_row(df_row=df_row)
        capture = EthAgentCaptureEntity(capture=df_row.capture,
                                        runid=df_row.runid,
                                        test_category=df_row.test_category,
                                        dut=dut,
                                        lp=lp,
                                        environment=environment,
                                        )
        return capture

    @classmethod
    def from_dict(cls, adict: dict) -> EthAgentCaptureEntity:
        dut = DUTTrafficFileEntity.from_dict(adict=adict.pop(
            "dut"))
        lp = LPTrafficFileEntity.from_dict(adict=adict.pop(
            "lp"))
        environment = CaptureEnvironmentFileEntity.from_dict(
            adict=adict.pop("environment"))
        capture = EthAgentCaptureEntity(capture=adict["capture"],
                                        runid=adict["runid"],
                                        test_category=adict["test_category"],
                                        dut=dut,
                                        lp=lp,
                                        environment=environment,
                                        )
        return capture

    def get_filter(self) -> dict:
        return {"capture": self.capture,
                "runid": self.runid,
                "test_category": self.test_category}

    @classmethod
    def search_filter(cls, capture: int, runid: int,
                      test_category: str) -> dict:
        search_dict = {}

        if test_category is not None:
            search_dict["test_category"] = test_category
        if capture is not None:
            search_dict['capture'] = int(capture)
        if runid is not None:
            search_dict['runid'] = int(runid)

        return search_dict

    def to_result(self) -> OrderedDict:
        environment = self.environment.to_result()
        dut = self.dut.to_result()
        lp = self.lp.to_result()
        result_dict = OrderedDict([("Capture", self.capture)])
        result_dict.update(environment)
        result_dict.update(lp)
        result_dict.update(dut)
        return result_dict


@dataclass
class _WaveformBase:
    testpoint: str
    runid: int
    capture: int
    test_category: str
    units: str
    location: str
    scope_channel: int
    steady_state_min: float = None
    steady_state_mean: float = None
    steady_state_max: float = None
    steady_state_pk2pk: float = None
    _steady_state_index: int = None
    spec_max: float = None
    spec_min: float = None
    max: float = None
    min: float = None
    user_reviewed: bool = False
    edge: bool = None
    associated_rail: str = None
    associated_rail_ss_index: int = None
    downsample: list = field(default_factory=list, repr=False)
    _type: str = "WAVEFORM"
    ID_FMT = "{testpoint}_{test}_{runid}_{capture}_CH{scope_channel}"


@dataclass()
class WaveformEntity(_EntityBase, _WaveformBase, Entity):

    def __post_init__(self):
        if self._id is None:
            self._id = self.format_id(
                testpoint=self.testpoint,
                test_category=self.test_category,
                runid=self.runid,
                capture=self.capture,
                scope_channel=self.scope_channel)

    @property
    def descriptor(self) -> str:
        return self.testpoint

    @classmethod
    def format_id(cls, testpoint: str, test_category: str, runid: int,
                  capture: int, scope_channel: int) -> str:
        test_category = cls.format_test_category(word=test_category)
        return cls.ID_FMT.format(testpoint=testpoint,
                                 test=test_category, runid=runid,
                                 capture=capture,
                                 scope_channel=scope_channel)

    def get_filter(self) -> dict:
        return {"testpoint": self.testpoint,
                "runid": self.runid,
                "capture": self.capture,
                "test_category": self.test_category,
                "scope_channel": self.scope_channel}

    @classmethod
    def search_filter(cls, testpoint: str, capture: int, runid: int,
                      test_category: str, scope_channel: int) -> dict:
        return {"testpoint": testpoint,
                "capture": capture,
                "runid": runid,
                "test_category": test_category,
                "scope_channel": scope_channel
                }

    def x_axis(self):
        return self.downsample[0]

    def y_axis(self):
        return self.downsample[1]

    def steady_state_index(self, expected_voltage: float = None) -> int:
        if self._steady_state_index is not None and expected_voltage is None:
            return self._steady_state_index
        if expected_voltage is None or np.isnan(expected_voltage):
            expected_voltage = self.steady_state_mean * 0.9  # 90%
        y = np.array(self.y_axis())
        cut_off = np.argmax(y >= expected_voltage)
        self._steady_state_index = cut_off
        return self._steady_state_index

    def set_steady_state_index(self, index: int) -> None:
        self._steady_state_index = index

    def to_result(self) -> OrderedDict:
        return OrderedDict([
            ("Scope Channel", self.scope_channel),
            ("Testpoint", self.testpoint),
            (f"Min ({self.units})", self.min),
            (f"Max ({self.units})", self.max),
            (f"Steady State Min ({self.units})", self.steady_state_min),
            (f"Steady State Mean ({self.units})", self.steady_state_mean),
            (f"Steady State Max ({self.units})", self.steady_state_max),
            (f"Steady State Pk2Pk ({self.units})", self.steady_state_pk2pk),
            ("User Reviewed WF?", self.user_reviewed),
            ("Waveform Location", self.location)
        ])

    def x_axis_in_milliseconds(self) -> np.array:
        x_axis = np.array(self.x_axis())
        x_axis_ms = x_axis * 1000
        return x_axis_ms

    def is_current_rail(self) -> bool:
        pass

