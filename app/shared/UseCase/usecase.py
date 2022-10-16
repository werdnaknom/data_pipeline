import typing as t

import pandas as pd
import os
from pathlib import Path

from app.shared.Responses.response import ResponseFailure, Response, \
    ResponseSuccess
from app.shared.Requests.requests import RequestObject

from app import globalConfig


class UseCase(object):
    config = globalConfig
    _name: str = "UseCase"

    def execute(self, request_object: RequestObject) -> Response:
        '''
        execute validates the request object.  If valid, tries "process 
        request".  If invalid, returns Response failure.
        
        Do not modify execute in child classes
        '''
        if not request_object:
            return ResponseFailure.build_from_invalid_request_object(
                request_object)

        try:
            return self.process_request(request_object)
        except Exception as exc:
            raise exc
            return ResponseFailure.build_system_error(
                "{}: {}".format(exc.__class__.__name__, "{}".format(exc)))

    def process_request(self, request_object: RequestObject) -> Response:
        '''
        Process request is the actual function that is run when a usecase is 
        executed.
        
        This function should be modified in child classes
        
        Returns:: Response object, either success or failure
        
        '''
        raise NotImplementedError(
            "process_request() not implemented by UseCase class"
        )

    def format_response(self, sheets: t.List[t.Tuple[str, pd.DataFrame]]) -> \
            ResponseSuccess:
        response_value = []
        for sheet_name, df in sheets:
            response_value.append((sheet_name, df.to_json()))

        return ResponseSuccess(value=response_value)

    def get_result_directory(self) -> Path:
        # return Path(os.environ.get("RESULT_FOLDER"))
        return Path(self.config.RESULTS_FOLDER)

    def build_output_path_from_dict(self, adict: dict, depth: str) -> Path:
        """
        Takes in a dictionary and returns a Path object down to the depth
        keyword. The path is created if it does not already exist prior to
        returning the path object.

        @param adict: Dictionary containing keys in the accepted depth list.
        @param depth: How deep to build the folder structure.
        @return:
        """
        accepted_depth = ['dut', 'pba', 'rework', 'submission', 'runid',
                          'capture', 'testpoint']
        assert depth in accepted_depth, f"depth [{depth}] must be in {accepted_depth}"
        result_path = self.get_result_directory()

        for d in accepted_depth:
            result_path.joinpath(adict[d])
            if d == depth:
                break

        result_path = result_path.joinpath(self._name)
        result_path.mkdir(parents=True, exist_ok=True)
        return result_path

    def build_output_path_from_row(self, df_row: pd.Series, depth: str) -> Path:
        """
        Will return a Path Object created from the depth keyword and df_row
        input objects.  The path will be created before the path object is
        returned.

        @param df_row: Series object from raw dataframe object containing the accepted_depth keywords
        @param depth: string containing one of the accepted_depth keywords
        @return:
        """
        row_dict = {
            "dut": df_row["dut"],
            "pba": df_row["pba"],
            "rework": str(df_row["rework"]),
            "submission": df_row["submission"],
            "runid": str(df_row["runid"]),
            "capture": str(df_row["capture"]),
            "testpoint": str(df_row["testpoint"])
        }

        return self.build_output_path_from_dict(adict=row_dict, depth=depth)
