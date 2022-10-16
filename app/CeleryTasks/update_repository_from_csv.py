import typing as t

import pandas as pd

from celery_worker import celeryapp
from celery import Task

from app.CeleryTasks.celery_task_base_class import CeleryTaskBaseClass

from app.UseCases.Entity_Uploading.csv_to_repo_usecase import \
    WaveformCSVToRepositoryUseCase, TrafficCSVToRepositoryUseCase, \
    CSVToRepoRequestObject
from app.Repository.repository import Repository, MongoRepository


class UpdateMongoRepositoryTask(CeleryTaskBaseClass):
    _file_prefix: str = "UpdateMongo"
    uc = None

    def run(self, *args, **kwargs):
        req = kwargs["request_object"]
        uc = self.uc(repo=MongoRepository())
        resp = uc.execute(request_object=req)
        if resp:
            df = resp.value
            df_path_pkl = self.df_to_pickle(df=df)
            df_path_str = self.path_to_str(path=df_path_pkl)
            return df_path_str
        else:
            raise resp


class WaveformUpdateMongoRepositoryTask(UpdateMongoRepositoryTask):
    _file_prefix: str = "WaveformUpdateMongo"
    uc = WaveformCSVToRepositoryUseCase


class TrafficUpdateMongoRepositoryTask(UpdateMongoRepositoryTask):
    _file_prefix: str = "TrafficUpdateMongo"
    uc = TrafficCSVToRepositoryUseCase


@celeryapp.task(bind=True, base=UpdateMongoRepositoryTask,
                name='waveform_update_mongo')
def waveform_update_mongo(*args, **kwargs):
    # df_json = kwargs["df_json"]
    # request_obj = CSVToRepoRequestObject(df_json=df_json)
    df_path = kwargs["df_path_str"]
    request_obj = CSVToRepoRequestObject(df_path_str=df_path)
    df_path_str = WaveformUpdateMongoRepositoryTask().run(
        request_object=request_obj)
    # if resp:
    # return resp.value.to_json()
    # return resp
    return df_path_str


@celeryapp.task(bind=True, base=UpdateMongoRepositoryTask,
                name='traffic_update_mongo')
def traffic_update_mongo(*args, **kwargs):
    df_path = kwargs["df_path_str"]
    request_obj = CSVToRepoRequestObject(df_path_str=df_path)
    df_path_str = TrafficUpdateMongoRepositoryTask().run(
        request_object=request_obj)
    return df_path_str
