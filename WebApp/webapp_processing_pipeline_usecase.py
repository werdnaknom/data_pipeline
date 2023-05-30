from Entities.UseCase import UseCase
from Entities.RequestResponse import Responses, RequestObject, ResponseSuccess, ResponseFailure

from Entities.config import PostProcessingConfig

from Entities.RequestResponse.WebappProcessingRequest.webapp_processing_request import WebAppProcessingRequest


class WebAppProcessingPipelineUseCase(UseCase):
    config = PostProcessingConfig()

    def process_request(self, request_object: WebAppProcessingRequest) -> Responses:
        for test in self.config.post_processors:
            raise NotImplementedError
