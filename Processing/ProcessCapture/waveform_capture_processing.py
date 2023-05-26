import typing as t
from Entities.UseCase import UseCase
from Entities.RequestResponse import RequestObject, Responses, ResponseSuccess, ResponseFailure
from Entities.Helpers.path_translator import PathTranslator
from Entities.Entities.entities import WaveformCaptureEntity


class ProcessWaveformCaptureRequestObject(RequestObject):

    def __init__(self):
        chamber_temperature: int
        waveform_names: t.List[str]
        waveform_binary_paths: t.List[PathTranslator]
        voltages: t.Dict[int, dict]
        capture: int
        runid: str
        runid_status: str
        compress: bool

    @classmethod
    def from_mongo(cls, adict):
        return cls.from_dict(adict=adict)

    @classmethod
    def from_dict(cls, adict):
        raise NotImplementedError


class ProcessWaveformCapture(UseCase):

    def process_request(self, request_object: RequestObject) -> Responses:
        raise NotImplementedError
