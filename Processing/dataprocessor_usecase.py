import logging
import typing as t

import pandas as pd

from Entities.RequestResponse import ResponseFailure, ResponseSuccess

logging.basicConfig(format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)s] : %(message)s',
                    level=logging.DEBUG)

LOG_LEVEL = logging.DEBUG


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


class DataProcessor:

    @classmethod
    def log(cls):
        logging_handler = logging.getLogger(cls.__name__)
        return logging_handler

    def execute(self) -> t.Union[ProcessorResponseSuccess, ProcessorResponseFailure]:
        """
        Process the input dataframe and return the processed dataframe.
        This method needs to be implemented in a subclass.
        """
        raise NotImplementedError


class DataFrameProcessor(DataProcessor):

    def __init__(self):
        self.returns_modified: bool = False
        self.dataframe_name: str = None

    def _process_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Process the input dataframe and return the processed dataframe.
        This method needs to be implemented in a subclass.
        """
        raise NotImplementedError("process_dataframe method must be implemented in a subclass.")

    def execute(self, dataframe: pd.DataFrame) -> t.Union[ProcessorResponseSuccess, ProcessorResponseFailure]:
        self.log().debug("Starting execute")
        if not isinstance(dataframe, pd.DataFrame):
            msg = f"Execute input was not a dataframe, was {type(dataframe)}"
            self.log().debug(msg)
            return ProcessorResponseFailure(message=msg)
        else:
            processed_dataframe = self._process_dataframe(dataframe=dataframe)
            if isinstance(processed_dataframe, pd.DataFrame):
                return ProcessorResponseSuccess(dataframe=processed_dataframe, title=self.dataframe_name)
            else:
                return ProcessorResponseFailure(message=f"Postprocessor {self.dataframe_name} failed")


class ModifiedDataFrameProcessor(DataFrameProcessor):
    def __init__(self):
        super().__init__()

    def _process_dataframe(self, dataframe):
        # Modify the input DataFrame in-place
        dataframe["ModifiedColumn"] = dataframe["SomeColumn"] * 2
        return dataframe


class NewDataFrameProcessor(DataFrameProcessor):
    def __init__(self):
        super().__init__()
        self.returns_modified = False

    def _process_dataframe(self, dataframe):
        # Create a completely new DataFrame with some processing logic
        processed_dataframe = dataframe.copy()
        processed_dataframe["NewColumn"] = processed_dataframe["Column1"] + processed_dataframe["Column2"]
        return processed_dataframe
