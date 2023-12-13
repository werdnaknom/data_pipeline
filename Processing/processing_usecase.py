import typing as t
from config import Config
from flask import jsonify
import requests
from io import BytesIO
import json

from dataclasses import dataclass, field, asdict
from typing import Optional
import pandas as pd
from multiprocessing import Pool

from Entities.UseCase import UseCase
from Entities.RequestResponse import RequestObject, Responses, ResponseSuccess
from Entities.Entities.entities import TestpointEntity, RunidEntity, WaveformEntity


@dataclass
class TestpointInfoRequestObject(RequestObject):
    product: str
    testpoint: str
    test_category: str
    runid_status: Optional[t.List[str]] = field(default_factory=lambda: ["Complete"])
    runid: Optional[t.List[str]] = None
    pba: Optional[str] = None
    environment: Optional[dict] = None


@dataclass
class RunidInfoRequestObject(RequestObject):
    product: str
    runid: int
    test_category: str
    runid_status: t.List[str] = field(default_factory=lambda: ["Complete"])
    temperature: t.Optional[int] = None
    voltages: t.Optional[dict] = None
    testpoints: t.Optional[dict] = None
    optional_values: t.List[str] = field(default_factory=lambda: ["temperature", "testpoints", "voltages"])

    def to_dict(self) -> t.Dict:
        adict = {
            "product": self.product,
            "runid": self.runid,
            "test_category": self.test_category,
            "runid_status": self.runid_status
        }
        for optional in self.optional_values:
            attr = self.__getattribute__(name=optional)
            if attr:
                adict[optional] = attr
        return adict

    def match_query(self) -> t.Dict:
        return {
            "project": self.product,
            "runid": self.runid,
            "status.status": {"$in": self.runid_status}
        }


@dataclass
class TestpointQueryRequestObject(RequestObject):
    product: str
    testpoint_list: t.Optional[t.List[str]] = None

    def to_dict(self) -> t.Dict:
        adict = {
            "product": self.product
        }
        if self.testpoint_list:
            adict["testpoint_list"] = self.testpoint_list
        return adict

    def match_query(self) -> t.Dict:
        adict = {
            "product": self.product,
        }
        if self.testpoint_list:
            adict["testpoint"] = {"$in": self.testpoint_list}
        return adict


class ProcessingUseCase(UseCase):

    def process_request(self, request_object: TestpointInfoRequestObject) -> Responses:
        # Query the Repository
        repo_response = self.query_repository(request_object=request_object)
        # Clean up the repository response and turn it into a dataframe
        df = self._query_to_dataframe(repo_response=repo_response)

        excel_bytes = self.create_excel_sheets(input_dataframe=df)

        return ResponseSuccess(value=excel_bytes)

    def _query_to_dataframe(self, repo_response: str):
        data = json.loads(repo_response)['result']
        df = pd.json_normalize(data)
        return df

    def create_excel_sheets(self, input_dataframe: pd.DataFrame) -> bytes:
        '''
        :param dataframe:
        :return:
        '''
        excel_bytes = self._create_excel(sheets={
            "Testpoint": input_dataframe
        })
        raise NotImplementedError
        return excel_bytes

    def _create_excel(self, sheets: t.Dict[str, pd.DataFrame]) -> bytes:
        excel_output = BytesIO()
        writer = pd.ExcelWriter(excel_output, engine="xlsxwriter")
        for sheet_name, df in sheets.items():
            df.to_excel(excel_writer=writer, sheet_name=sheet_name, index=False)
        writer.close()
        excel_bytes = excel_output.getvalue()
        return excel_bytes

    def query_repository(self, request_object: TestpointInfoRequestObject, route="testpoint_review"):
        json_data = json.dumps(asdict(request_object))
        repo_url = Config.REPOSITORY_URL  # "http://127.0.0.1:5001"
        if route:
            repo_url = f"{repo_url}/api/{route}"
        print(repo_url)

        # Set the headers for the request (specify the content type as JSON)
        headers = {"Content-Type": "application/json"}

        # Send the request with the JSON data
        response = requests.post(repo_url, headers=headers, data=json_data)
        print(response.status_code)
        return response.text

    def query_testpoints(self, testpoint_request: TestpointQueryRequestObject) -> t.List[TestpointEntity]:
        json_data = json.dumps(testpoint_request.to_dict())
        '''
        repo_url = Config.REPOSITORY_URL
        repo_url = f"{repo_url}/api/testpoint_query"
        print(repo_url)

        # Set the headers for the request (specify the content type as JSON)
        headers = {"Content-Type": "application/json"}

        # Send the request with the JSON data
        response = requests.post(repo_url, headers=headers, data=json_data)
        print(response.status_code)
        return response.text
        '''
        import pymongo
        from config import Config
        client = pymongo.MongoClient('mongodb://192.168.1.226:27017/')
        # client = pymongo.MongoClient('mongodb://npoflask.jf.intel.com:27017/')
        db = client['ATS2']
        collection = db[TestpointEntity.get_type()]
        testpoint_entities = []
        # for testpoint_dict in collection.find(testpoint_request.match_query()):
        tp_query = testpoint_request.match_query()
        for testpoint_dict in collection.find(tp_query):
            testpointEntity = TestpointEntity.from_dict(adict=testpoint_dict)
            testpoint_entities.append(testpointEntity)

        return testpoint_entities

    def query_runid(self, runid_request: RunidInfoRequestObject) -> t.List[TestpointEntity]:
        '''
        json_data = json.dumps(runid_request.to_dict())
        repo_url = Config.REPOSITORY_URL
        repo_url = f"{repo_url}/api/testpoint_query"
        print(repo_url)

        # Set the headers for the request (specify the content type as JSON)
        headers = {"Content-Type": "application/json"}

        # Send the request with the JSON data
        response = requests.post(repo_url, headers=headers, data=json_data)
        print(response.status_code)
        return response.text
        '''
        import pymongo
        from config import Config
        client = pymongo.MongoClient('mongodb://192.168.1.226:27017/')
        # client = pymongo.MongoClient('mongodb://npoflask.jf.intel.com:27017/')
        db = client['ATS2']
        collection = db[RunidEntity.get_type()]
        runid_match_query = runid_request.match_query()
        pipeline = [
            {"$match": runid_match_query},
            {"$project": {"runid": 1, "pba": 1, "project": 1, "rework": 1, "status.status": 1, "serial": 1}},

            # Lookup tests that match each runid
            {"$lookup": {
                "from": WaveformEntity.get_type(),
                "let": {"runid": "$runid"},
                "pipeline": [
                    {"$match": {"$expr": {"$and": [
                        {"$eq": ["$runid", "$$runid"]},
                        {"$eq": ["$test_category", runid_request.test_category]}
                    ],
                    }}},
                    {"$project": {"capture": 1, "test_category": 1, "testpoint": 1,
                                  "steady_state_min": 1, "steady_state_mean": 1, "steady_state_max": 1,
                                  "steady_state_pk2pk": 1, "_steady_state_index": 1, "max": 1, "min": 1,
                                  "location": 1}},
                    {"$sort": {"capture": 1}},
                ],
                "as": "waveforms"
            }},
            {"$unwind": "$waveforms"},
        ]
        mongo_response = collection.aggregate(pipeline=pipeline)
        df = pd.json_normalize(list(mongo_response))

        return df
