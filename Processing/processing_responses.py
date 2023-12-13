import pandas as pd

from Entities.RequestResponse import ResponseFailure, ResponseSuccess


class ProcessorResponseFailure(ResponseFailure):
    def __init__(self, message):
        super(ProcessorResponseFailure, self).__init__(type_=self.PARAMETERS_ERROR, message=message)

    def _format_message(self, msg):
        if isinstance(msg, Exception):
            return "{}: {}".format(msg.__class__.__name__, "{}".format(msg))
        return msg


class ProcessorResponseSuccess(ResponseSuccess):

    def __init__(self, dataframe: pd.DataFrame, title: str):
        super(ProcessorResponseSuccess, self).__init__(value=dataframe)
        self.type = self.SUCCESS
        self.value = dataframe
        self.title = title

    @property
    def dataframe(self):
        return self.value
