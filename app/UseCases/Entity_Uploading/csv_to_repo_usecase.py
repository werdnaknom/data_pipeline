import time
import typing as t

import pandas as pd

from app.Repository.repository import Repository
from app.shared.UseCase.usecase import UseCase
from app.shared.Requests.requests import ValidRequestObject
from app.shared.Responses.response import Response, ResponseSuccess
from app.shared.Entities.entities import WaveformEntity

from .analyze_waveform_usecase import AnalyzeWaveformUseCase, \
    AnalyzeWaveformRequestObject

from .entity_to_repo_usecase import ProjectIDUseCase, PBAIDUseCase, \
    ReworkIDUseCase, SubmissionIDUseCase, RunIDUseCase, \
    WaveformCaptureIDUseCase, EthAgentCaptureIDUseCase, \
    AutomationTestIDUseCase, EntityIDUseCase

from .entity_upload_request_objects import ProjectIDRequestObject, \
    PBAIDRequestObject, ReworkIDRequestObject, SubmissionIDRequestObject, \
    RunIDRequestObject, AutomationTestRequestObject, EntityIDRequestObject, \
    WaveformCaptureRequestObject, EthAgentCaptureRequestObject


def timing_val(funct):
    def wrapper(*args, **kwargs):
        t1 = time.time()
        res = funct(*args, **kwargs)
        t2 = time.time()
        timer = t2 - t1
        print(f"{funct.__name__}: {timer}")
        return res

    return wrapper


class CSVToRepoRequestObject(ValidRequestObject):
    df: pd.DataFrame

    # def __init__(self, df_json: str):
    #    self.df = pd.read_json(df_json)
    def __init__(self, df_path_str: str):
        self.df = pd.read_pickle(df_path_str)


class CSVToRepositoryUseCase(UseCase):
    repo: Repository
    COLUMN_PRODUCT_ID: str = "product_id"
    COLUMN_PBA_ID: str = "pba_id"
    COLUMN_REWORK_ID: str = "rework_id"
    COLUMN_SUBMISSION_ID: str = "submission_id"
    COLUMN_RUN_ID: str = "run_id"
    COLUMN_AUTOMATION_ID: str = "automation_id"
    COLUMN_DATACAPTURE_ID: str = "datacapture_id"
    COLUMN_WAVEFORM_ID: str = "waveform_id"

    def __init__(self, repo: Repository):
        self.repo = repo
        self.output_df = pd.DataFrame(columns=[
            self.COLUMN_PRODUCT_ID,
            self.COLUMN_PBA_ID,
            self.COLUMN_REWORK_ID,
            self.COLUMN_SUBMISSION_ID,
            self.COLUMN_RUN_ID,
            self.COLUMN_AUTOMATION_ID,
            self.COLUMN_DATACAPTURE_ID,
            self.COLUMN_WAVEFORM_ID
        ])

    def process_request(self,
                        request_object: CSVToRepoRequestObject) -> Response:

        df = request_object.df

        # Find or upload Projects.  Add "project_id" field to datafile
        resp = self._find_or_upload_projects(data_file=df)

        # Find or upload PBAs.  Add "pba_id" field to datafile
        resp = self._find_or_upload_pbas(data_file=df)

        # Find or upload Reworks.  Add "rework_id" field to datafile
        resp = self._find_or_upload_reworks(data_file=df)

        # Find or upload Submissions.  Add "submission_id" field to datafile
        resp = self._find_or_upload_submissions(data_file=df)

        # Find or upload runid.  Add "run_id" field to datafile
        resp = self._find_or_upload_runids(data_file=df)

        # Find or upload automation test.  Add "automation_id" field to datafile
        resp = self._find_or_upload_automation_test(data_file=df)

        # Find or upload capture.  Add "datacapture_id" field to datafile
        resp = self._find_or_upload_captures(data_file=df)

        # Find or Upload all waveform files
        # Adds a column "WaveformEntity_id" that has the ID for
        # each row_dict's waveform entity.
        resp = self._find_or_upload_waveforms(data_file=df)

        return ResponseSuccess(value=df)

    def groupby_filter_to_dict(self, filter: tuple, by: list) -> dict:
        result = {}
        for key, value in zip(by, filter):
            result[key] = value
        return result

    def _find_or_upload(self, data_file: pd.DataFrame,
                        by: list, column_name: str,
                        use_case: EntityIDUseCase,
                        req_object: EntityIDRequestObject) -> None:

        data_file[column_name] = None

        for filt, df in data_file.groupby(by=by):
            if df.empty:
                continue
            row_zero = df.iloc[0]
            req = req_object(row=row_zero)
            resp = use_case.execute(request_object=req)

            if not resp:
                raise resp.value

            data_file.at[df.index.to_list(), column_name] = resp.value

    @timing_val
    def _find_or_upload_projects(self, data_file: pd.DataFrame) -> Response:
        uc = ProjectIDUseCase(repo=self.repo)
        by = ['dut']
        resp = self._find_or_upload(data_file=data_file,
                                    by=by, column_name=self.COLUMN_PRODUCT_ID,
                                    use_case=uc,
                                    req_object=ProjectIDRequestObject)
        return resp

    @timing_val
    def _find_or_upload_pbas(self, data_file: pd.DataFrame) -> Response:
        uc = PBAIDUseCase(repo=self.repo)
        by = ['dut', 'pba']

        resp = self._find_or_upload(data_file=data_file,
                                    by=by, column_name=self.COLUMN_PBA_ID,
                                    use_case=uc,
                                    req_object=PBAIDRequestObject)
        return resp

    @timing_val
    def _find_or_upload_reworks(self, data_file: pd.DataFrame) -> Response:
        uc = ReworkIDUseCase(repo=self.repo)
        by = ['pba', 'rework']
        resp = self._find_or_upload(data_file=data_file,
                                    by=by, column_name=self.COLUMN_REWORK_ID,
                                    use_case=uc,
                                    req_object=ReworkIDRequestObject)

        return resp

    @timing_val
    def _find_or_upload_submissions(self, data_file: pd.DataFrame) -> Response:
        uc = SubmissionIDUseCase(repo=self.repo)
        by = ['pba', 'rework', "serial_number"]

        resp = self._find_or_upload(data_file=data_file,
                                    by=by,
                                    column_name=self.COLUMN_SUBMISSION_ID,
                                    use_case=uc,
                                    req_object=SubmissionIDRequestObject)

        return resp

    @timing_val
    def _find_or_upload_runids(self, data_file: pd.DataFrame) -> Response:
        uc = RunIDUseCase(repo=self.repo)
        by = ["runid"]
        resp = self._find_or_upload(data_file=data_file,
                                    by=by, column_name=self.COLUMN_RUN_ID,
                                    use_case=uc,
                                    req_object=RunIDRequestObject)

        return resp

    @timing_val
    def _find_or_upload_automation_test(self,
                                        data_file: pd.DataFrame) -> Response:
        uc = AutomationTestIDUseCase(repo=self.repo)
        by = ["test_category"]
        resp = self._find_or_upload(data_file=data_file,
                                    by=by,
                                    column_name=self.COLUMN_AUTOMATION_ID,
                                    use_case=uc,
                                    req_object=AutomationTestRequestObject)

        return resp

    @timing_val
    def _find_or_upload_captures(self, data_file: pd.DataFrame) -> Response:
        ''' See Child Classes'''
        raise NotImplementedError

    @timing_val
    def _find_or_upload_waveforms(self, data_file: pd.DataFrame) -> Response:
        ''' See Child Classes '''
        raise NotImplementedError

    '''
    @timing_val
    def _find_or_upload_waveforms(self, data_file: pd.DataFrame) -> Response:
        """
        
        @param data_file: 
        @return: 
        """

        uc = AnalyzeWaveformUseCase(repo=self.repo)

        data_file[self.COLUMN_WAVEFORM_ID] = data_file.apply(
            func=self.funct_process_waveform, args=(uc,),
            axis='columns')
        return ResponseSuccess(value=data_file)

    '''

    def funct_process_waveform(self, row: pd.Series,
                               uc: AnalyzeWaveformUseCase) -> \
            WaveformEntity:
        """
        
        @param row: 
        @param uc: 
        @return: 
        """
        # print(row_dict)
        req = AnalyzeWaveformRequestObject(df_row=row)
        uc_resp = uc.execute(request_object=req)

        return uc_resp.value


class WaveformCSVToRepositoryUseCase(CSVToRepositoryUseCase):
    @timing_val
    def _find_or_upload_captures(self, data_file: pd.DataFrame) -> Response:
        uc = WaveformCaptureIDUseCase(repo=self.repo)
        by = ["test_category", "runid", "capture"]

        resp = self._find_or_upload(data_file=data_file,
                                    by=by,
                                    column_name=self.COLUMN_DATACAPTURE_ID,
                                    use_case=uc,
                                    req_object=WaveformCaptureRequestObject)

        return resp

    @timing_val
    def _find_or_upload_waveforms(self, data_file: pd.DataFrame) -> Response:
        # num_df_rows = len(data_file.index)
        uc = AnalyzeWaveformUseCase(repo=self.repo)

        groupby_tuples = data_file.groupby(by=["runid", "capture"])

        for _, chunked_df in groupby_tuples:
            print(chunked_df.shape)
            chunked_df[self.COLUMN_WAVEFORM_ID] = chunked_df.apply(
                func=self.funct_process_waveform, args=(uc,),
                axis='columns')

            data_file.at[chunked_df.index, self.COLUMN_WAVEFORM_ID] = \
                chunked_df[self.COLUMN_WAVEFORM_ID]

        # print(data_file[self.COLUMN_WAVEFORM_ID])

class TrafficCSVToRepositoryUseCase(CSVToRepositoryUseCase):
    @timing_val
    def _find_or_upload_captures(self, data_file: pd.DataFrame) -> Response:
        uc = EthAgentCaptureIDUseCase(repo=self.repo)
        by = ["test_category", "runid", "capture"]

        resp = self._find_or_upload(data_file=data_file,
                                    by=by,
                                    column_name=self.COLUMN_DATACAPTURE_ID,
                                    use_case=uc,
                                    req_object=EthAgentCaptureRequestObject)

        return resp

    @timing_val
    def _find_or_upload_waveforms(self, data_file: pd.DataFrame) -> Response:
        """
        There are no waveform_names in a traffic test
        @param data_file:
        @return:
        """
        pass
