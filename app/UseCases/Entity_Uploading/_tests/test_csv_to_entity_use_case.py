from unittest import mock
import inspect
from basicTestCase.basic_test_case import BasicTestCase

from app.UseCases.Entity_Uploading.csv_to_entity_use_case import \
    EntityIDRequestObject, RequestToEntityObject, \
    RequestToAutomationTestEntity, RequestToDataCaptureEntity, \
    RequestToPBAEntity, RequestToProjectEntity, RequestToReworkEntity, \
    RequestToRunidEntity, RequestToSubmissionEntity

from app.UseCases.Entity_Uploading.entity_upload_request_objects import *

from app.shared.Entities.entities import *


class CSVtoEntityTestCase(BasicTestCase):
    entity: Entity = None
    uc = None
    req = None

    def _setUp(self):
        self.csv_file = self._helper_load_input_load_profile_df()
        self.row = self.csv_file.iloc[0]

    def _helper_test_create(self):
        req = self.req(row=self.row)
        uc = self.uc()
        entity = uc.create_entity(request_object=req)
        self.assertIsInstance(entity, self.entity)
        return entity

    def test_process_request(self):
        uc = RequestToEntityObject()
        mock_return_value = Entity()

        req = EntityIDRequestObject()
        with mock.patch(
                'app.UseCases.Entity_Uploading.csv_to_entity_use_case'
                '.RequestToEntityObject.create_entity'
        ) as mock_create:
            mock_create.return_value = mock_return_value
            resp = uc.process_request(request_object=req)

            mock_create.assert_called_once_with(request_object=req)

        self.assertTrue(resp)
        self.assertEqual(mock_return_value, resp.value)


class ProjectTestCase(CSVtoEntityTestCase):
    entity = ProjectEntity
    uc = RequestToProjectEntity
    req = ProjectIDRequestObject

    def test_create_entity(self):
        self._helper_test_create()


class PBATestCase(CSVtoEntityTestCase):
    entity = PBAEntity
    uc = RequestToPBAEntity
    req = PBAIDRequestObject

    def test_create_entity(self):
        self._helper_test_create()


class ReworkTestCase(CSVtoEntityTestCase):
    entity = ReworkEntity
    uc = RequestToReworkEntity
    req = ReworkIDRequestObject

    def test_create_entity(self):
        self._helper_test_create()


class SubmissionTestCase(CSVtoEntityTestCase):
    entity = SubmissionEntity
    uc = RequestToSubmissionEntity
    req = SubmissionIDRequestObject

    def test_create_entity(self):
        self._helper_test_create()


class RunidTestCase(CSVtoEntityTestCase):
    entity = RunidEntity
    uc = RequestToRunidEntity
    req = RunIDRequestObject

    def test_create_entity(self):
        self._helper_test_create()


class AutomationTestTestCase(CSVtoEntityTestCase):
    entity = AutomationTestEntity
    uc = RequestToAutomationTestEntity
    req = AutomationTestRequestObject

    def test_create_entity(self):
        self._helper_test_create()


class DataCaptureTestCase(CSVtoEntityTestCase):
    entity = WaveformCaptureEntity
    uc = RequestToDataCaptureEntity
    req = DataCaptureRequestObject

    def test_create_entity(self):
        self._helper_test_create()


'''
class WaveformTestCase(CSVtoEntityTestCase):
    entity = WaveformEntity
    uc = RequestToWaveformEntity
    req = WaveformRequestObject

    def test_create_entity(self):
        self._helper_test_create()
'''
