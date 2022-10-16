import typing as t
import os

import pymongo
from app.shared.Entities.entities import *

# TODO:: REMOVE THIS FOR PRODUCTION
import mongomock


class Repository(object):
    _db_name = "PostProcessing"
    _client = None
    PROJECT_COLLECTION = ProjectEntity._type
    PBA_COLLECTION = PBAEntity._type
    REWORK_COLLECTION = ReworkEntity._type
    SUBMISSION_COLLECTION = SubmissionEntity._type
    RUNID_COLLECTION = RunidEntity._type
    AUTOMATIONTEST_COLLECTION = AutomationTestEntity._type
    WAVEFORM_CAPTURE_COLLECTION = WaveformCaptureEntity._type
    TRAFFIC_CAPTURE_COLLECTION = EthAgentCaptureEntity._type
    WAVEFORM_COLLECTION = WaveformEntity._type

    ''' PROPERTIES '''

    @property
    def db(self):
        return self._client[self._db_name]

    @property
    def collection_project(self):
        return self.db[self.PROJECT_COLLECTION]

    @property
    def collection_pba(self):
        return self.db[self.PBA_COLLECTION]

    @property
    def collection_rework(self):
        return self.db[self.REWORK_COLLECTION]

    @property
    def collection_submission(self):
        return self.db[self.SUBMISSION_COLLECTION]

    @property
    def collection_runid(self):
        return self.db[self.RUNID_COLLECTION]

    @property
    def collection_automation_test(self):
        return self.db[self.AUTOMATIONTEST_COLLECTION]

    @property
    def collection_waveform_capture(self):
        return self.db[self.WAVEFORM_CAPTURE_COLLECTION]

    @property
    def collection_traffic_capture(self):
        return self.db[self.TRAFFIC_CAPTURE_COLLECTION]

    @property
    def collection_waveform(self):
        return self.db[self.WAVEFORM_COLLECTION]

    ''' FUNCTIONS '''

    def get_collection(self, collection):
        return self.db[collection]

    def _find_id(self, collection, filters: dict) -> str:
        # TODO:: CLEAN UP!!
        # return {}
        id_key = "_id"
        found = collection.find_one(filters, {id_key: 1})
        if found is None:
            return ""
        else:
            return found[id_key]

    def _find_one(self, collection, filters: dict) -> dict:
        # TODO:: CLEAN UP!!
        # return {}
        return collection.find_one(filters)

    def _find(self, collection, filters: dict) -> t.List[dict]:
        return list(collection.find(filters))

    def _find_many(self, filters: t.List[dict], collection, **kwargs) -> t.List[
        dict]:
        found = []
        for filter in filters:
            one = self._find_one(collection=collection, filters=filter)
            found.append(one)
        return found

    def insert_one(self, entity: Entity) -> pymongo.results.InsertOneResult:
        # TODO:: CLEAN UP!!
        # print(entity)
        # return entity.to_dict()
        collection = self.get_collection(collection=entity.get_collection())
        entity_dict = entity.to_dict()

        inserted = collection.insert_one(entity_dict)
        return inserted.inserted_id

    def insert_waveform(self, entity: WaveformEntity) -> str:
        collection = self.get_collection(collection=entity.get_collection())

        entity_dict = entity.to_dict()
        if entity_dict.get('downsample'):
            entity_dict['downsample'] = [wf.tolist() for wf in entity_dict[
                'downsample']]
        inserted = collection.insert_one(entity_dict)
        return inserted.inserted_id

    def find_capture_waveforms(self, test_category: str, runid: int,
                               capture: int):
        filters = {"test_category": test_category,
                   "runid": runid,
                   "capture": capture}

        collection = self.get_collection(WaveformEntity.get_collection())
        return self.find_many(collection=collection,
                              filters=filters)

    def insert_or_update(self, entity: Entity) -> dict:
        collection = self.get_collection(collection=entity.get_collection())

        entity_dict = entity.to_dict()
        entity_dict["$set"] = {"modified_date": datetime.datetime.utcnow()}

        update = collection.update_one(key=entity.get_filter(),
                                       update=entity_dict,
                                       upsert=True)
        return update

    def _query(self, collection, filters: dict, projection: dict = None) -> \
            t.List[dict]:
        if projection:
            return collection.find(filters, projection)
        return collection.find(filters)

    ''' Project '''

    def find_project(self, project_name: str) -> dict:
        filters = ProjectEntity.search_filter(name=project_name)
        return self._find_one(collection=self.collection_project,
                              filters=filters)

    def find_project_id(self, project_name: str) -> str:
        filters = ProjectEntity.search_filter(name=project_name)
        inserted_id = self._find_id(collection=self.collection_project,
                                    filters=filters)
        return inserted_id

    def query_projects(self, filters: dict, projections: dict = None) -> \
            t.List[dict]:
        query = self._query(collection=self.collection_project,
                            filters=filters, projection=projections)
        return query

    ''' PBA '''

    def find_pba(self, part_number: str, project: str) -> dict:
        filters = PBAEntity.search_filter(part_number=part_number,
                                          project=project)
        return self._find_one(collection=self.collection_pba, filters=filters)

    def find_pba_id(self, part_number: str, project: str) -> str:
        filters = PBAEntity.search_filter(part_number=part_number,
                                          project=project)
        filters.pop("project")
        inserted_id = self._find_id(collection=self.collection_pba,
                                    filters=filters)
        return inserted_id

    def query_pbas(self, filters: dict, projections: dict = None) -> \
            t.List[dict]:
        query = self._query(collection=self.collection_pba,
                            filters=filters, projection=projections)
        return query

    ''' REWORK '''

    def find_rework(self, rework_number: int, pba: str) -> dict:
        filters = ReworkEntity.search_filter(rework=rework_number, pba=pba)
        return self._find_one(collection=self.collection_rework,
                              filters=filters)

    def find_rework_id(self, pba: str, rework_number: int) -> str:
        filters = ReworkEntity.search_filter(rework=rework_number, pba=pba)
        inserted_id = self._find_id(collection=self.collection_rework,
                                    filters=filters)
        return inserted_id

    def query_reworks(self, filters: dict, projections: dict = None) -> \
            t.List[dict]:
        query = self._query(collection=self.collection_rework,
                            filters=filters, projection=projections)
        return query

    ''' SUBMISSION '''

    def find_submission(self, descriptor: str, pba: str, rework: int) -> dict:
        filters = SubmissionEntity.search_filter(descriptor=descriptor,
                                                 pba=pba,
                                                 rework=rework)
        return self._find_one(collection=self.collection_submission,
                              filters=filters)

    def find_submission_id(self, submission: str, pba: str, rework: int) -> \
            str:
        filters = SubmissionEntity.search_filter(submission=submission,
                                                 pba=pba,
                                                 rework=rework)
        inserted = self._find_id(collection=self.collection_submission,
                                 filters=filters)
        return inserted

    def query_submissions(self, filters: dict, projections: dict = None) -> \
            t.List[dict]:
        query = self._query(collection=self.collection_submission,
                            filters=filters, projection=projections)
        return query

    ''' RUNID '''

    def find_runid(self, runid: int) -> dict:
        filters = RunidEntity.search_filter(runid=runid)
        return self._find_one(collection=self.collection_runid,
                              filters=filters)

    def find_run_id(self, runid: int) -> str:
        filters = RunidEntity.search_filter(runid=runid)
        inserted = self._find_id(collection=self.collection_runid,
                                 filters=filters)
        return inserted

    def query_runids(self, filters: dict, projections: dict = None) -> \
            t.List[dict]:
        query = self._query(collection=self.collection_runid,
                            filters=filters, projection=projections)
        return query

    ''' AUTOMATION TEST_NAME '''

    def find_automation_test(self, test_name: str) -> dict:
        filters = AutomationTestEntity.search_filter(name=test_name)
        return self._find_one(collection=self.collection_automation_test,
                              filters=filters)

    def find_automation_test_id(self, test_name: str) -> str:
        filters = AutomationTestEntity.search_filter(name=test_name)
        id = self._find_id(collection=self.collection_automation_test,
                           filters=filters)
        return id

    def query_automation_tests(self, filters: dict, projections: dict = None) \
            -> \
                    t.List[dict]:
        query = self._query(collection=self.collection_automation_test,
                            filters=filters, projection=projections)
        return query

    ''' WAVEFORM DATA CAPTURE '''

    def find_waveform_capture_one(self, test: str, runid: int,
                                  capture: int) -> dict:
        filters = WaveformCaptureEntity.search_filter(capture=capture,
                                                      runid=runid,
                                                      test_category=test)
        return self._find_one(collection=self.collection_waveform_capture,
                              filters=filters)

    def find_waveform_captures_many(self, test: str = None, runid: int = None,
                                    capture: int = None,
                                    additional_filters: dict = None) -> \
            t.List:

        filters = WaveformCaptureEntity.search_filter(capture=capture,
                                                      runid=runid,
                                                      test_category=test)
        if additional_filters:
            filters.update(additional_filters)
        return self._find(filters=filters,
                          collection=self.collection_waveform_capture)

    def find_waveform_capture_id(self, capture: int, runid: int,
                                 test: str) -> str:
        filters = WaveformCaptureEntity.search_filter(capture=capture,
                                                      runid=runid,
                                                      test_category=test)
        return self._find_id(collection=self.collection_waveform_capture,
                             filters=filters)

    def distinct_waveform_capture_temp_setpoints(self, filters: dict):
        return self.collection_waveform_capture.distinct(
            "environment.chamber_setpoint", filters)

    def distinct_waveform_capture_slew_rates(self, filters: dict):
        return self.collection_waveform_capture.distinct(
            "environment.power_supply_channels", filters)

    def query_waveform_captures(self, filters: dict,
                                projections: dict = None) -> \
            t.List[dict]:
        query = self._query(collection=self.collection_waveform_capture,
                            filters=filters, projection=projections)
        return query

    ''' TRAFFIC DATA CAPTURE '''

    def find_traffic_capture_one(self, test: str, runid: int, capture: int) -> \
            dict:
        filters = EthAgentCaptureEntity.search_filter(capture=capture,
                                                      runid=runid,
                                                      test_category=test)
        return self._find_one(collection=self.collection_traffic_capture,
                              filters=filters)

    def find_traffic_captures_many(self, test: str = None, runid: int = None,
                                   capture: int = None,
                                   additional_filters: dict = None) -> \
            t.List:

        filters = EthAgentCaptureEntity.search_filter(capture=capture,
                                                      runid=runid,
                                                      test_category=test)
        if additional_filters:
            filters.update(additional_filters)
        return self._find(filters=filters,
                          collection=self.collection_traffic_capture)

    def find_traffic_capture_id(self, capture: int, runid: int,
                                test: str) -> str:
        filters = EthAgentCaptureEntity.search_filter(capture=capture,
                                                      runid=runid,
                                                      test_category=test)
        return self._find_id(collection=self.collection_traffic_capture,
                             filters=filters)

    def distinct_traffic_capture_temp_setpoints(self, filters: dict):
        return self.collection_traffic_capture.distinct(
            "environment.chamber_setpoint", filters)

    def distinct_traffic_capture_slew_rates(self, filters: dict):
        return self.collection_traffic_capture.distinct(
            "environment.power_supply_channels", filters)

    def query_traffic_captures(self, filters: dict,
                               projections: dict = None) -> \
            t.List[dict]:
        query = self._query(collection=self.collection_traffic_capture,
                            filters=filters, projection=projections)
        return query

    ''' TESTPOINT '''

    def find_waveform(self, testpoint: str, capture: int, runid: int,
                      test_category: str, scope_channel: int) -> dict:
        filters = WaveformEntity.search_filter(testpoint=testpoint,
                                               capture=capture,
                                               runid=runid,
                                               scope_channel=scope_channel,
                                               test_category=test_category)
        return self._find_one(collection=self.collection_waveform,
                              filters=filters)

    def find_waveform_by_id(self, waveform_id):
        filters = {"_id": waveform_id}
        return self._find_one(collection=self.collection_waveform,
                              filters=filters)

    def find_waveform_id(self, testpoint: str, capture: int, runid: int,
                         test_category: str, scope_channel: int) -> str:
        filters = WaveformEntity.search_filter(testpoint=testpoint,
                                               capture=capture,
                                               runid=runid,
                                               scope_channel=scope_channel,
                                               test_category=test_category)
        return self._find_id(collection=self.collection_waveform,
                             filters=filters)

    def find_many_waveforms(self, list_of_filters: t.List[dict]) -> t.List[
        dict]:
        return self._find_many(collection=self.collection_waveform,
                               filters=list_of_filters)

    def find_waveforms_by_runid(self, runid: int,
                                test_category: str) -> t.List[dict]:
        filters = {"runid": int(runid),
                   "test_category": test_category}
        return self._find(collection=self.collection_waveform,
                          filters=filters)

    def query_waveforms(self, filters: dict, projections: dict = None) -> \
            t.List[dict]:
        query = self._query(collection=self.collection_waveform,
                            filters=filters, projection=projections)
        return query


class MongoRepository(Repository):

    # USE "True" DURING DEVELOPMENT. CHANGE TO "False" FOR PRODUCTION
    def __init__(self, mongo_uri: str = None, debug=False):
        if not debug:
            if mongo_uri is None:
                mongo_uri = self.__get_mongo_uri()
            self._mongo_uri = mongo_uri
            self._client = pymongo.MongoClient(mongo_uri)
        else:
            if mongo_uri is None:
                mongo_uri = self.__get_mock_mongo_uri()
            self._mongo_uri = mongo_uri
            self._client = self.connect_to_mock_mongo()

    def __get_mock_mongo_uri(self):
        mongo_uri = "server.example.com"
        return mongo_uri

    @mongomock.patch(servers=(("server.example.com", 27017),))
    def connect_to_mock_mongo(self):
        return pymongo.MongoClient(self._mongo_uri)

    def __get_mongo_uri(self):
        try:
            mongo_uri = os.environ.get("MONGO_URI")
        except RuntimeError:
            mongo_uri = os.environ.get("MONGO_URI") or \
                        "mongodb://localhost:27017"
        return mongo_uri
