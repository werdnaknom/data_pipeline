import typing as t
import time
import json
from collections import OrderedDict

import pandas as pd

from celery import Task, current_task

from celery_worker import celeryapp
from .post_processing_task import WaveformPostProcessingBaseTask
import typing as t
import time
import json
from collections import OrderedDict

import pandas as pd

from celery import Task, current_task

from celery_worker import celeryapp
from .post_processing_task import WaveformPostProcessingBaseTask
from app.UseCases.Automation_Tests_UseCases.inrush import InrushUseCase, \
    AutomationTestRequestObject

from app.Repository.repository import MongoRepository


class InrushTask(WaveformPostProcessingBaseTask):
    _file_prefix: str = "Inrush"
    test = "Inrush"

    def run_post_processing(self, df: pd.DataFrame, filter_by: str) -> \
            t.OrderedDict[str, pd.DataFrame]:
        req = AutomationTestRequestObject(df=df,
                                          filter_by=filter_by)

        uc = InrushUseCase(repo=MongoRepository())
        result = uc.execute(request_object=req)

        return result.value


@celeryapp.task(name='inrush')
def inrush_task(*args, **kwargs):
    print("INRUSH TASK RECEIVED!")
    result = InrushTask().run(*args, **kwargs)
    return result
