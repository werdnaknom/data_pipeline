import logging
import typing as t

import pandas as pd

from Processing.processing_responses import ProcessorResponseFailure, ProcessorResponseSuccess
from Processing.processing_usecase import TestpointQueryRequestObject
from Processing.RepoProcessors import TestPointProcessor

logging.basicConfig(format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)s] : %(message)s',
                    level=logging.DEBUG)

LOG_LEVEL = logging.DEBUG


class DataProcessor:

    @classmethod
    def log(cls):
        logging_handler = logging.getLogger(cls.__name__)
        return logging_handler

    def _waveform_names(self, dataframe: pd.DataFrame) -> t.List[str]:
        testpoints = dataframe["waveforms.testpoint"].unique()
        self.log().debug(f"dataframe unique testpoints: {testpoints}")
        return testpoints.tolist()

    def _product_name(self, dataframe: pd.DataFrame) -> str:
        return dataframe["project"].unique()[0]

    def _query_dataframe_testpoints(self, dataframe: pd.DataFrame):
        test_points = self._waveform_names(dataframe=dataframe)
        product = self._product_name(dataframe=dataframe)
        return self._query_testpoints(product=product, testpoint_list=test_points)

    def _query_testpoints(self, product: str, testpoint_list: t.Optional[t.List[str]] = None) -> pd.DataFrame:
        test_point_request_object = TestpointQueryRequestObject(product=product, testpoint_list=testpoint_list)
        repo = TestPointProcessor()
        response = repo.execute(json_request=test_point_request_object.to_dict())
        if response:
            return response.dataframe
        else:
            return response

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
