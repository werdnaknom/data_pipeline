from Entities.UseCase import UseCase
from Entities.RequestResponse import Responses, RequestObject, ResponseSuccess, ResponseFailure


class WebAppProcessingUseCase(UseCase):

    def process_request(self, request_object: RequestObject) -> Responses:
        pass

