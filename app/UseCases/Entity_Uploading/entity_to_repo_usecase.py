import pandas as pd

from app.Repository.repository import Repository
from app.shared.UseCase.usecase import UseCase
from app.shared.Responses.response import Response, ResponseSuccess
from app.shared.Requests.requests import ValidRequestObject
from app.shared.Entities.entities import *

from app.UseCases.Entity_Uploading.entity_upload_request_objects import \
    EntityIDRequestObject, ProjectIDRequestObject, DataCaptureRequestObject, \
    ReworkIDRequestObject, RunIDRequestObject, PBAIDRequestObject, \
    AutomationTestRequestObject, SubmissionIDRequestObject

from app.UseCases.Entity_Uploading.csv_to_entity_use_case import \
    RequestToProjectEntity, RequestToDataCaptureEntity, \
    RequestToAutomationTestEntity, RequestToRunidEntity, \
    RequestToSubmissionEntity, RequestToReworkEntity, RequestToPBAEntity, \
    RequestToEthAgentCaptureEntity, RequestToWaveformCaptureEntity


class EntityIDUseCase(UseCase):
    entity: Entity

    def __init__(self, repo: Repository):
        self.repo = repo

    def process_request(self, request_object: EntityIDRequestObject) \
            -> Response:
        entity_id = self.get_entity_id(request_object=request_object)
        return ResponseSuccess(value=entity_id)

    def get_entity_id(self, request_object: EntityIDRequestObject) -> str:
        entity_id = self.query_entity_id(request_object=request_object)

        if entity_id:
            return entity_id
        else:
            entity = self.create_entity(request_object=request_object)

            inserted_id = self.insert_entity(entity=entity)
            return inserted_id

    def query_entity_id(self, request_object: EntityIDRequestObject) -> str:
        raise NotImplementedError

    def create_entity(self, request_object: EntityIDRequestObject) -> Entity:
        raise NotImplementedError

    def insert_entity(self, entity: Entity) -> str:
        inserted_id = self.repo.insert_one(entity=entity)
        return inserted_id

    def _validate_response(self, resp):
        if resp:
            return resp.value
        else:
            raise resp.value


'''

PROJECT ID

'''


class ProjectIDUseCase(EntityIDUseCase):

    def query_entity_id(self, request_object: ProjectIDRequestObject) -> str:
        id = self.repo.find_project_id(project_name=request_object.project_name)
        return id

    def create_entity(self,
                      request_object: ProjectIDRequestObject) -> ProjectEntity:
        uc = RequestToProjectEntity()
        resp = uc.execute(request_object=request_object)
        return self._validate_response(resp=resp)


'''

PBA ID

'''


class PBAIDUseCase(EntityIDUseCase):

    def query_entity_id(self, request_object: PBAIDRequestObject) -> str:
        id = self.repo.find_pba_id(part_number=request_object.part_number,
                                   project=request_object.project_name)
        return id

    def create_entity(self,
                      request_object: PBAIDRequestObject) -> PBAEntity:
        uc = RequestToPBAEntity()
        resp = uc.execute(request_object=request_object)
        return self._validate_response(resp=resp)


'''

REWORK 

'''


class ReworkIDUseCase(EntityIDUseCase):

    def query_entity_id(self, request_object: ReworkIDRequestObject) -> str:
        id = self.repo.find_rework_id(rework_number=request_object.rework,
                                      pba=request_object.part_number)
        return id

    def create_entity(self,
                      request_object: ReworkIDRequestObject) -> ReworkEntity:
        uc = RequestToReworkEntity()
        resp = uc.execute(request_object=request_object)
        return self._validate_response(resp=resp)


'''

Submission 

'''


class SubmissionIDUseCase(EntityIDUseCase):

    def query_entity_id(self, request_object: SubmissionIDRequestObject) -> str:
        id = self.repo.find_submission_id(submission=request_object.submission,
                                          pba=request_object.part_number,
                                          rework=request_object.rework)
        return id

    def create_entity(self,
                      request_object: SubmissionIDRequestObject) -> SubmissionEntity:
        uc = RequestToSubmissionEntity()
        resp = uc.execute(request_object=request_object)
        return self._validate_response(resp=resp)


'''

Runid 

'''


class RunIDUseCase(EntityIDUseCase):

    def query_entity_id(self, request_object: RunIDRequestObject) -> str:
        id = self.repo.find_run_id(runid=request_object.runid)
        return id

    def create_entity(self,
                      request_object: RunIDRequestObject) -> RunidEntity:
        uc = RequestToRunidEntity()
        resp = uc.execute(request_object=request_object)
        return self._validate_response(resp=resp)


'''

    AUTOMATION TEST_NAME

'''


class AutomationTestIDUseCase(EntityIDUseCase):

    def query_entity_id(self,
                        request_object: AutomationTestRequestObject) -> str:
        id = self.repo.find_automation_test_id(
            test_name=request_object.test_name)
        return id

    def create_entity(self, request_object: AutomationTestRequestObject) \
            -> AutomationTestEntity:
        uc = RequestToAutomationTestEntity()
        resp = uc.execute(request_object=request_object)
        return self._validate_response(resp=resp)


'''

    DATACAPTURE

'''


class DataCaptureIDUseCase(EntityIDUseCase):
    '''
        Datacaptures could be one of:
            1) EthAgent Capture
            2) Waveform Capture
        Depending on the test.
    '''

    def process_request(self, request_object: DataCaptureRequestObject) \
            -> Response:
        if request_object.test_category == "EthAgent":
            uc = EthAgentCaptureIDUseCase(repo=self.repo)
        else:
            uc = WaveformCaptureIDUseCase(repo=self.repo)
        entity_id = uc.get_entity_id(request_object=request_object)
        return ResponseSuccess(value=entity_id)


class EthAgentCaptureIDUseCase(EntityIDUseCase):
    def query_entity_id(self,
                        request_object: DataCaptureRequestObject) -> str:
        id = self.repo.find_traffic_capture_id(capture=request_object.capture,
                                               runid=request_object.runid,
                                               test=request_object.test_category)
        return id

    def create_entity(self, request_object: DataCaptureRequestObject) \
            -> EthAgentCaptureEntity:
        uc = RequestToEthAgentCaptureEntity()
        resp = uc.execute(request_object=request_object)
        return self._validate_response(resp=resp)


class WaveformCaptureIDUseCase(EntityIDUseCase):

    def query_entity_id(self,
                        request_object: DataCaptureRequestObject) -> str:
        id = self.repo.find_waveform_capture_id(capture=request_object.capture,
                                                runid=request_object.runid,
                                                test=request_object.test_category)
        return id

    def create_entity(self, request_object: DataCaptureRequestObject) \
            -> WaveformCaptureEntity:
        uc = RequestToWaveformCaptureEntity()
        resp = uc.execute(request_object=request_object)
        return self._validate_response(resp=resp)


'''

Create waveform is in the "analyze Waveform Use case" file

'''
