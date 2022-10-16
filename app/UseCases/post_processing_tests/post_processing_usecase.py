from pathlib import Path
import platform
import time

import celery

from app.shared.Responses.response import ResponseSuccess, Response
from app.shared.UseCase.usecase import UseCase
from app.UseCases.Entity_Uploading.analyze_waveform_usecase import \
    AnalyzeWaveformRequestObject, AnalyzeWaveformUseCase
from app.Repository.repository import Repository


PROJECT_ID = "project_id"
PBA_ID = "pba_id"
REWORK_ID = "rework_id"
SUBMISSION_ID = "submission_id"
RUN_ID = "run_id"
AUTOMATION_ID = "automation_test_id"
DATACAPTURE_ID = "datacapture_id"
WAVEFORM_ID = "waveform_id"

def timing_val(funct):
    def wrapper(*args, **kwargs):
        t1 = time.time()
        res = funct(*args, **kwargs)
        t2 = time.time()
        timer = t2-t1
        print(f"{funct.__name__}: {timer}")
        return res
    return wrapper


class PostProcessingWaveFormUseCase(UseCase):
    pass
    """
    SPEC_MAX: str = "spec_max"  # Max do not cross line
    SPEC_MIN: str = "spec_min"  # Minimum do not cross line
    EXPECTED_NOMINAL: str = "expected_nominal"  # Expected voltage
    EDGE_RAIL: str = "edge_rail"  # Edge (True) or On-board (False) Rail
    # What edge rail generates this signal (primarily voltage edge rails,
    # except for voltage edge rails where it's the current edge)
    ASSOCIATED_EDGE_RAIL: str = "associated_rail"
    CURRENT_RAIL: str = "current_rail"

    def __init__(self, repo: Repository):
        self.repo = repo

    def process_request(self, request_object: PostProcessingRequest) \
            -> Response:
        user_path = Path(request_object.user_input_file_path)
        user_input = self.load_dataframe_from_xlsx(
            xlsx_path=user_path)

        data_path = Path(request_object.data_file_path)
        data_file = self.load_dataframe_from_csv(
            csv_path=data_path)
        # Covert //npo to /npo for the web server
        #data_file = self._convert_path_strings_to_server(data_file=data_file)
        # fix "wrong" rail names from user file:
        # Note -- all replacements are done inplace so returned data_file is
        # not strictly necessary

        data_file = self._cleanup_rail_names(user_file=user_input,
                                             data_file=data_file)
        # Identify Edge Voltage and Current Rails
        # Add expected values and spec max to dataframe
        data_file = self._identify_edge_rails(user_file=user_input,
                                              data_file=data_file)

        # Add testpoint estimated value and min/max values
        data_file = self._add_testpoint_criteria(user_file=user_input,
                                                 data_file=data_file)




        # Find or upload Projects.  Add "project_id" field to datafile
        resp = self._find_or_upload_projects(data_file=data_file)
        if not resp:
            return resp

        # Find or upload PBAs.  Add "pba_id" field to datafile
        resp = self._find_or_upload_pbas(data_file=data_file)
        if not resp:
            return resp

        # Find or upload Reworks.  Add "rework_id" field to datafile
        resp = self._find_or_upload_reworks(data_file=data_file)
        if not resp:
            return resp

        # Find or upload Submissions.  Add "submission_id" field to datafile
        resp = self._find_or_upload_submissions(data_file=data_file)
        if not resp:
            return resp

        # Find or upload runid.  Add "run_id" field to datafile
        resp = self._find_or_upload_runids(data_file=data_file)
        if not resp:
            return resp

        # Find or upload capture.  Add "datacapture_id" field to datafile
        resp = self._find_or_upload_captures(data_file=data_file)
        if not resp:
            return resp

        # Find or Upload all waveform files
        # Adds a column "WaveformEntity_id" that has the ID for
        # each row's waveform entity.
        resp = self._find_or_upload_waveforms(data_file=data_file)
        '''
        task_group = group(waveform_task.s("repo", "", df.to_json())
                           for _, df in data_file.groupby(by=["runid",
            "capture"]))
        res = task_group()
        print(res.get())
        '''

        return resp


    def groupby_filter_to_dict(self, filter: tuple, by: list) -> dict:
        result = {}
        for key, value in zip(by, filter):
            result[key] = value
        return result

    def _find_or_upload(self, data_file: pd.DataFrame,
                        by: list, column_name: str,
                        use_case: EntityIDUseCase,
                        req_object: EntityIDRequestObject) -> Responses:

        data_file[column_name] = None

        for filt, df in data_file.groupby(by=by):
            #print(filt)
            if df.empty:
                continue
            row_zero = df.iloc[0]
            req = req_object(row=row_zero)
            resp = use_case.execute(request_object=req)

            if not resp:
                return resp

            data_file.at[df.index.to_list(), column_name] = resp.value

        return ResponseSuccess(value=None)

    @timing_val
    def _find_or_upload_projects(self, data_file: pd.DataFrame) -> Responses:
        uc = ProjectIDUseCase(repo=self.repo)
        by = ['dut']
        resp = self._find_or_upload(data_file=data_file,
                                    by=by, column_name=PROJECT_ID,
                                    use_case=uc,
                                    req_object=ProjectIDRequestObject)
        return resp

    @timing_val
    def _find_or_upload_pbas(self, data_file: pd.DataFrame) -> Responses:
        uc = PBAIDUseCase(repo=self.repo)
        by = ['dut', 'pba']
        resp = self._find_or_upload(data_file=data_file,
                                    by=by, column_name=PBA_ID,
                                    use_case=uc,
                                    req_object=PBAIDRequestObject)
        return resp

    @timing_val
    def _find_or_upload_reworks(self, data_file: pd.DataFrame) -> Responses:
        uc = ReworkIDUseCase(repo=self.repo)
        by = ['pba', 'rework']
        resp = self._find_or_upload(data_file=data_file,
                                    by=by, column_name=REWORK_ID,
                                    use_case=uc,
                                    req_object=ReworkIDRequestObject)

        return resp

    @timing_val
    def _find_or_upload_submissions(self, data_file: pd.DataFrame) -> Responses:
        uc = SubmissionIDUseCase(repo=self.repo)
        by = ['pba', 'rework', "serial_number"]

        resp = self._find_or_upload(data_file=data_file,
                                    by=by, column_name=SUBMISSION_ID,
                                    use_case=uc,
                                    req_object=SubmissionIDRequestObject)

        return resp

    @timing_val
    def _find_or_upload_runids(self, data_file: pd.DataFrame) -> Responses:
        uc = RunIDUseCase(repo=self.repo)
        by = ["runid"]
        resp = self._find_or_upload(data_file=data_file,
                                    by=by, column_name=RUN_ID,
                                    use_case=uc,
                                    req_object=RunIDRequestObject)

        return resp

    @timing_val
    def _find_or_upload_automation_test(self,
                                        data_file: pd.DataFrame) -> Responses:
        uc = AutomationTestUseCase(repo=self.repo)
        by = ["test_category"]
        resp = self._find_or_upload(data_file=data_file,
                                    by=by, column_name=AUTOMATION_ID,
                                    use_case=uc,
                                    req_object=AutomationTestRequestObject)

        return resp

    @timing_val
    def _find_or_upload_captures(self, data_file: pd.DataFrame) -> Responses:
        uc = DataCaptureUseCase(repo=self.repo)
        by = ["test_category", "runid", "capture"]

        resp = self._find_or_upload(data_file=data_file,
                                    by=by, column_name=DATACAPTURE_ID,
                                    use_case=uc,
                                    req_object=DataCaptureRequestObject)

        return resp



    @timing_val
    def _find_or_upload_waveforms(self, data_file: pd.DataFrame) -> Responses:

        uc = AnalyzeWaveformUseCase(repo=self.repo)

        data_file['WaveformEntity_id'] = data_file.apply(
            func=self.funct_process_waveform, args=(uc,),
            axis='columns')
        return ResponseSuccess(value=data_file)

    def funct_process_waveform(self, row: pd.Series,
                               uc: AnalyzeWaveformUseCase) -> \
            WaveformEntity:
        # print(row)
        req = AnalyzeWaveformRequestObject(df_row=row)
        uc_resp = uc.execute(request_object=req)

        return uc_resp.value

    def _cleanup_rail_names(self, user_file: t.OrderedDict[str, pd.DataFrame],
                            data_file: pd.DataFrame) -> pd.DataFrame:
        RAILS_TO_RENAME_SHEETNAME = "Rails to Rename"
        # TESTPOINT_NAME_COLUMN = "testpoint"

        name_rails_df = user_file[RAILS_TO_RENAME_SHEETNAME]

        split_names = name_rails_df.to_dict("split")
        '''Split returns :
        {'index': [0, 1, 2], 
        'columns': ['Wrong Name', 'Corrected Name'], 
        'data': [['0P1V_AVDDH', '1P1V_AVDDH'],
                ['test2', 'corrected_2'], 
                ['test3', 'corrected_3']]}
        '''
        for data in split_names['data']:
            wrong_name = data[0]
            right_name = data[1]
            data_file['testpoint'].replace(wrong_name, right_name, inplace=True)
            # If we want to replace the wrong name EVERYWHERE, we can run the
            # below code instead
            # data_file.replace(wrong_name, right_name, inplace=True)
        return data_file

    def _identify_edge_rails(self,
                             user_file: t.OrderedDict[str, pd.DataFrame],
                             data_file: pd.DataFrame) -> pd.DataFrame:
        EDGE_CHANNELS = "Edge Channels"
        edge_df = user_file[EDGE_CHANNELS]

        data_file[self.EDGE_RAIL] = False
        data_file[self.ASSOCIATED_EDGE_RAIL] = None
        data_file[self.SPEC_MAX] = np.NaN
        data_file[self.SPEC_MIN] = np.NaN
        data_file[self.EXPECTED_NOMINAL] = np.NaN
        data_file[self.CURRENT_RAIL] = False

        for i, row in edge_df.iterrows():
            # Update Voltage Rows
            data_file.loc[
                data_file.testpoint == row.Voltage, self.EDGE_RAIL] = True
            data_file.loc[
                data_file.testpoint == row.Voltage,
                self.ASSOCIATED_EDGE_RAIL] = row.Current
            data_file.loc[
                data_file.testpoint == row.Voltage,
                self.EXPECTED_NOMINAL] = row["Nominal Voltage (V)"]

            # Update Current Rows
            data_file.loc[
                data_file.testpoint == row.Current, self.EDGE_RAIL] = True
            data_file.loc[
                data_file.testpoint == row.Current,
                self.ASSOCIATED_EDGE_RAIL] = row.Voltage
            data_file.loc[data_file.testpoint == row.Current,
                          self.SPEC_MAX] = row['Max Current (A)']
            data_file.loc[data_file.testpoint == row.Current,
                          self.CURRENT_RAIL] = True

        return data_file

    @timing_val
    def _convert_path_strings_to_server(self, data_file: pd.DataFrame) -> \
            pd.DataFrame:
        if platform.system() == "Linux":
            for i, row in data_file.iterrows():
                wf_location = row['location']
                if wf_location.find("//npo/coos/") == 0:
                    #Change location from //npo to /npo for linux server
                    data_file.at[i, "location"] = wf_location[1:]
        return data_file



    def _add_testpoint_criteria(self,
                                user_file: t.OrderedDict[str, pd.DataFrame],
                                data_file: pd.DataFrame) -> pd.DataFrame:
        ONBOARD_RAILS = "On-Board Rails"
        testpoint_df = user_file[ONBOARD_RAILS]

        for i, row in testpoint_df.iterrows():
            testpoint = row['Voltage Rail']
            data_file.loc[
                data_file.testpoint == testpoint, self.EXPECTED_NOMINAL] = \
                row['Nominal Value']
            data_file.loc[data_file.testpoint == testpoint, self.SPEC_MIN] = \
                row[
                    'Spec Min']
            data_file.loc[data_file.testpoint == testpoint, self.SPEC_MAX] = \
                row[
                    'Spec Max']
        return data_file

    def load_dataframe_from_csv(self, csv_path: Path) -> pd.DataFrame:
        file_suffix = ".csv"
        assert csv_path.suffix == file_suffix
        dataframe = pd.read_csv(csv_path)
        return dataframe

    def load_dataframe_from_xlsx(self, xlsx_path: Path) \
            -> t.OrderedDict[str, pd.DataFrame]:
        file_suffix = ".xlsx"
        assert xlsx_path.suffix == file_suffix
        # Sheet_name = None to return OrderedDict of dataframes from each
        # sheet
        df_dict = pd.read_excel(xlsx_path, sheet_name=None)
        return df_dict
    """


