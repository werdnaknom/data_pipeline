import typing as t
import time
import json
from collections import OrderedDict

import pandas as pd

from celery import Task, current_task

from celery_worker import celeryapp
from .post_processing_task import EthAgentPostProcessingBaseTask

from app.UseCases.Automation_Tests_UseCases.ber import BitErrorRatioUseCase, \
    AutomationTestRequestObject

from app.Repository.repository import MongoRepository


class BitErrorRatioTask(EthAgentPostProcessingBaseTask):
    test = "Bit Error Ratio"

    def run_post_processing(self, df: pd.DataFrame, filter_by: str) \
            -> t.OrderedDict[str, pd.DataFrame]:
        req = AutomationTestRequestObject(df=df,
                                          filter_by=filter_by)

        uc = BitErrorRatioUseCase(repo=MongoRepository())
        result = uc.execute(request_object=req)

        return result.value


@celeryapp.task(name='bit_error_ratio')
def bit_error_ratio_task(*args, **kwargs):
    print("BER TASK RECEIVED!")
    result = BitErrorRatioTask().run(*args, **kwargs)

    return result
