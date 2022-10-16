import typing as t
import time
import json
from collections import OrderedDict

import pandas as pd

from celery import Task, current_task

from celery_worker import celeryapp
from .post_processing_task import WaveformPostProcessingBaseTask
from app.UseCases.Automation_Tests_UseCases.sequencing import \
    SequencingUseCase, AutomationTestRequestObject

from app.Repository.repository import MongoRepository


class SequencingTask(WaveformPostProcessingBaseTask):
    test = "Sequencing"

    def run_post_processing(self, df: pd.DataFrame, filter_by: str) \
            -> t.OrderedDict[str, pd.DataFrame]:
        req = AutomationTestRequestObject(df=df,
                                          filter_by=filter_by)

        uc = SequencingUseCase(repo=MongoRepository())
        result = uc.execute(request_object=req)

        return result.value


@celeryapp.task(name='sequencing')
def sequencing_task(*args, **kwargs):
    print("SEQUENCING TASK RECEIVED!")
    result = SequencingTask().run(*args, **kwargs)
    return result
