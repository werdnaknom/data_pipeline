import typing as t
import json
import datetime as dt
import time
import os
import random
import string

from pathlib import Path

import pandas as pd

from celery import Task, current_task

from app.CeleryTasks.celery_task_base_class import CeleryTaskBaseClass

from app.CeleryTasks.cleanup_input_dataframe_tasks import waveform_cleanup, \
    WaveformDataFrameCleanUp, EthAgentDataFrameCleanup, traffic_cleanup
from app.CeleryTasks.update_repository_from_csv import \
    TrafficUpdateMongoRepositoryTask, traffic_update_mongo, \
    WaveformUpdateMongoRepositoryTask, waveform_update_mongo
from app.UseCases.Entity_Uploading.csv_to_repo_usecase import \
    CSVToRepoRequestObject


class PostProcessingBaseTask(CeleryTaskBaseClass):
    _file_prefix: str = "PostProcessBase"
    test: str = None
    PROGRESS_STATE = "PROGRESS"

    def post_process(self, path_str: str, filter_by: str) -> Path:
        df = self.pickle_load_str_df(pickle_str=path_str)
        celery_alive = self.celery_update_state(state=self.PROGRESS_STATE,
                                                current=8, total=10,
                                                status=
                                                f"Post Processing {len(df)} " \
                                                f"items with filter: "
                                                f"{filter_by}")
        result_df_path = self.run_post_processing(df=df, filter_by=filter_by)

        return result_df_path

    def run_post_processing(self, df: pd.DataFrame, filter_by: str) -> Path:
        """
        Need to override in child classes.

        @param df: Cleaned and with Entity ID dataframe
        @return: Returns a path object to the result excel file.

        """
        raise NotImplementedError

    def run(self, *args, **kwargs):
        request_dict = self.extract_request_paths(**kwargs)
        data_path = request_dict['data_path']
        config_path = request_dict['config_path']

        prepped_df_path_str = self.data_preparation(data_path=data_path,
                                                    config_path=config_path)

        post_processed_path: Path = self.post_process(
            path_str=prepped_df_path_str,
            filter_by=request_dict["filter_by"])
        # print("PATH", post_processed_path)

        formatted_result = self.format_response(df_path=post_processed_path)

        '''
        prepped_df: pd.DataFrame = self.data_preparation(data_path=data_path,
                                                         config_path=config_path)

        post_processed: t.OrderedDict[
            str, pd.DataFrame] = self.run_post_processing(df=prepped_df)

        formatted_result = self.format_response(data_dict=post_processed)
        '''

        return formatted_result

    def format_response(self, df_path: Path) -> dict:
        result = {'current': 100,
                  'total': 100,
                  'status': f'{self.test} completed!',
                  'result': self.path_to_str(df_path),
                  'filename': self.format_filename()}
        return result

    '''
    def format_response(self,
                        data_dict: t.OrderedDict[str, str]) -> dict:
        result = {'current': 100,
                  'total': 100,
                  'status': f'{self.test} ' 'completed!',
                  'result': data_dict,
                  'filename': self.format_filename()}
        return result
    '''

    def format_filename(self) -> str:
        return f"{self.test}_{dt.datetime.now()}"

    def extract_request_paths(self, **kwargs) -> t.Dict:
        """
        @param kwargs: keyword arguments include only "Request", which is a
        json dictionary of a request object from the Flask Frontend.
        @return:
            data_path --> JSON path of where the csv datafile is located
            config_path --> JSON path of where the user configuration datafile is located
        """
        request_str = kwargs["request"]
        request_dict = json.loads(request_str)
        data_path = request_dict["data_file_path"]
        config_path = request_dict["user_input_file_path"]
        test_name = request_dict['test_name']
        data_filename = request_dict["data_filename"]
        config_filename = request_dict["user_input_filename"]
        filter_by = request_dict["filter_by"]

        extracted_dict = {
            "test_name": test_name,
            "data_path": data_path,
            "data_filename": data_filename,
            "config_path": config_path,
            "config_filename": config_filename,
            "filter_by": filter_by,
        }

        return extracted_dict

    def data_preparation(self, data_path: str,
                         config_path: str) -> str:
        celery_alive = self.celery_update_state(state=self.PROGRESS_STATE,
                                                current=1, total=10,
                                                status="Preparing Input Data...")

        cleaned_df_path_str = self.data_prep_clean(data_path=data_path,
                                                   config_path=config_path)

        updated_df_path_str = self.data_prep_update_repository(
            df_path_str=cleaned_df_path_str)

        # df = pd.read_json(updated_df_json)

        return updated_df_path_str

    def data_prep_clean(self, data_path: str, config_path: str) -> str:
        celery_alive = self.celery_update_state(state=self.PROGRESS_STATE,
                                                current=1, total=10,
                                                status="Cleaning Input Data")
        ''' Runs "Cleanup Task" '''

        if celery_alive:
            cleaned_req = waveform_cleanup.apply_async(
                kwargs={"config_path": config_path,
                        "data_path": data_path})
            cleaned_df_path_str = cleaned_req.get()
        else:
            cleaned_df_path_str = WaveformDataFrameCleanUp().run(
                config_path=config_path,
                data_path=data_path)
        return cleaned_df_path_str

    # def data_prep_update_repository(self, json_df: str) -> str:
    def data_prep_update_repository(self, df_path_str: str) -> str:

        celery_alive = self.celery_update_state(state=self.PROGRESS_STATE,
                                                current=4, total=10,
                                                status="Updating Data Repository....")
        if celery_alive:
            '''
            #entity_df = update_mongo.apply_async(kwargs={"df_json": json_df})
            #updated_df_json = entity_df.get()
            #return updated_df_json
            '''
            entity_df = waveform_update_mongo.apply_async(kwargs={"df_path_str":
                                                                      df_path_str})
            updated_df_path_str = entity_df.get()
            return updated_df_path_str
        else:
            '''
            request_obj = CSVToRepoRequestObject(df_json=json_df)
            resp = UpdateMongoRepositoryTask().run(request_object=request_obj)
            if resp:
                return resp.value.to_json()
            return resp
            '''
            request_obj = CSVToRepoRequestObject(df_path_str=df_path_str)
            updated_df_path_str = WaveformUpdateMongoRepositoryTask().run(
                request_object=request_obj)
            return updated_df_path_str


class WaveformPostProcessingBaseTask(PostProcessingBaseTask):
    _file_prefix: str = "WaveformPostProcessBase"
    test: str = None
    PROGRESS_STATE = "PROGRESS"


class EthAgentPostProcessingBaseTask(PostProcessingBaseTask):

    def data_prep_clean(self, data_path: str, config_path: str) -> str:
        celery_alive = self.celery_update_state(state=self.PROGRESS_STATE,
                                                current=1, total=10,
                                                status="Cleaning Input Data")
        ''' Runs "Cleanup Task" '''

        if celery_alive:
            cleaned_req = traffic_cleanup.apply_async(
                kwargs={"config_path": config_path,
                        "data_path": data_path})
            cleaned_df_path_str = cleaned_req.get()
        else:
            cleaned_df_path_str = EthAgentDataFrameCleanup().run(
                config_path=config_path,
                data_path=data_path)
        return cleaned_df_path_str

    def data_prep_update_repository(self, df_path_str: str) -> str:

        celery_alive = self.celery_update_state(state=self.PROGRESS_STATE,
                                                current=4, total=10,
                                                status="Updating Data Repository....")
        if celery_alive:
            entity_df = traffic_update_mongo.apply_async(kwargs={"df_path_str":
                                                                     df_path_str})
            updated_df_path_str = entity_df.get()
            return updated_df_path_str
        else:
            request_obj = CSVToRepoRequestObject(df_path_str=df_path_str)
            updated_df_path_str = TrafficUpdateMongoRepositoryTask().run(
                request_object=request_obj)
            return updated_df_path_str
