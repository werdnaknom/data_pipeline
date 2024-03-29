import json
import typing

from config import Config
from Entities.config import PostProcessingConfig
import requests
import pandas as pd

from Processing.processing_responses import ProcessorResponseFailure, ProcessorResponseSuccess


class RepositoryProcessor:

    def __init__(self, url):
        self.url = url

    def _create_repository_api_url(self, route: str) -> str:
        url_fmt = "{host}{url_prefix}/{route}"
        host_url = Config.REPOSITORY_URL
        url_prefix = PostProcessingConfig.repository_dataprocessing_route
        url = url_fmt.format(host=host_url, url_prefix=url_prefix, route=route)
        return url

    def _query_repository(self, json_request: typing.Dict) -> ProcessorResponseSuccess | ProcessorResponseFailure:
        # Set the headers for the request (specify the content type as JSON)
        headers = {"Content-Type": "application/json"}

        response = requests.post(self.url, data=json.dumps(json_request),
                                 headers=headers)
        if response.status_code == 200:
            data = response.json()  # Website returns JSON data
            json_data = data['result']
            dataframe = pd.json_normalize(json_data)
            return ProcessorResponseSuccess(dataframe=dataframe,
                                            title="repository response")
        else:
            print("Failed to retrieve data from the website.")
            return ProcessorResponseFailure(
                message=f"Repository returned status code {response.status_code}. Failed to retrieve data from the repository")

    def execute(self, json_request: typing.Dict) -> ProcessorResponseSuccess | ProcessorResponseFailure:
        return self._query_repository(json_request=json_request)


class SequencingRepositoryProcessor(RepositoryProcessor):

    def __init__(self):
        url = self._create_repository_api_url(route="sequencing_processor")
        super().__init__(url=url)


class WaveformRepositoryProcessor(RepositoryProcessor):

    def __init__(self):
        url = self._create_repository_api_url(route="waveform_processor")
        super().__init__(url=url)


class TestPointProcessor(RepositoryProcessor):

    def __init__(self):
        url = self._create_repository_api_url(route="testpoint_definitions_processor")
        super().__init__(url=url)
