import pandas as pd

from app.Repository.repository import Repository
from app.shared.UseCase.usecase import UseCase
from app.shared.Responses.response import Response, ResponseSuccess
from app.shared.Requests.requests import ValidRequestObject
from app.shared.Entities.entities import *

from app.UseCases.Entity_Uploading.entity_upload_request_objects import \
    EntityIDRequestObject, ProjectIDRequestObject, DataCaptureRequestObject, \
    ReworkIDRequestObject, RunIDRequestObject, PBAIDRequestObject, \
    AutomationTestRequestObject, SubmissionIDRequestObject, \
    WaveformCaptureRequestObject, EthAgentCaptureRequestObject


class RequestToEntityObject(UseCase):
    entity: Entity

    def process_request(self, request_object: EntityIDRequestObject) \
            -> Response:
        entity = self.create_entity(request_object=request_object)
        return ResponseSuccess(value=entity)

    def create_entity(self, request_object: EntityIDRequestObject) -> Entity:
        raise NotImplementedError


'''

PROJECT ID

'''


class RequestToProjectEntity(RequestToEntityObject):

    def create_entity(self,
                      request_object: ProjectIDRequestObject) -> ProjectEntity:
        p = ProjectEntity(name=request_object.project_name,
                          silicon=request_object.silicon)
        return p


'''

PBA ID

'''


class RequestToPBAEntity(RequestToEntityObject):

    def create_entity(self,
                      request_object: PBAIDRequestObject) -> PBAEntity:
        p = PBAEntity(part_number=request_object.part_number,
                      project=request_object.project_name,
                      notes=request_object.notes,
                      reworks=request_object.reworks,
                      customers=request_object.customers)
        return p


'''

REWORK 

'''


class RequestToReworkEntity(RequestToEntityObject):

    def create_entity(self,
                      request_object: ReworkIDRequestObject) -> ReworkEntity:
        r = ReworkEntity(pba=request_object.part_number,
                         rework=request_object.rework,
                         notes=request_object.notes,
                         eetrack_id=request_object.eetrack_id)
        return r


'''

Submission 

'''


class RequestToSubmissionEntity(RequestToEntityObject):

    def create_entity(self,
                      request_object: SubmissionIDRequestObject) -> SubmissionEntity:
        s = SubmissionEntity(submission=request_object.submission,
                             rework=request_object.rework,
                             pba=request_object.part_number)
        return s


'''

Runid 

'''


class RequestToRunidEntity(RequestToEntityObject):

    def create_entity(self,
                      request_object: RunIDRequestObject) -> RunidEntity:
        r = RunidEntity(runid=request_object.runid,
                        comments=request_object.comments,
                        testrun=request_object.testrun,
                        status=request_object.status,
                        system_info=request_object.system_info
                        )
        return r


'''

    AUTOMATION TEST_NAME
  
'''


class RequestToAutomationTestEntity(RequestToEntityObject):

    def create_entity(self, request_object: AutomationTestRequestObject) \
            -> AutomationTestEntity:
        r = AutomationTestEntity(name=request_object.test_name,
                                 notes=request_object.notes)
        return r


'''

    DATACAPTURE

'''


class RequestToDataCaptureEntity(RequestToEntityObject):
    def create_entity(self, request_object: DataCaptureRequestObject) \
            -> WaveformCaptureEntity:
        r = DataCaptureEntity(capture=request_object.capture,
                              runid=request_object.runid,
                              test_category=request_object.test_category,
                              capture_settings=request_object.settings,
                              environment=request_object.environment_configuration)
        return r


class RequestToWaveformCaptureEntity(RequestToEntityObject):

    def create_entity(self, request_object: WaveformCaptureRequestObject) \
            -> WaveformCaptureEntity:
        r = WaveformCaptureEntity(capture=request_object.capture,
                                  runid=request_object.runid,
                                  test_category=request_object.test_category,
                                  capture_settings=request_object.settings,
                                  environment=request_object.environment_configuration)
        return r


class RequestToEthAgentCaptureEntity(RequestToEntityObject):

    def create_entity(self, request_object: EthAgentCaptureRequestObject) \
            -> EthAgentCaptureEntity:
        r = EthAgentCaptureEntity(capture=request_object.capture,
                                  runid=request_object.runid,
                                  test_category=request_object.test_category,
                                  dut=request_object.dut,
                                  lp=request_object.lp,
                                  environment=request_object.environment_configuration)
        return r


'''

Create waveform is in the "analyze Waveform Use case" file

'''
