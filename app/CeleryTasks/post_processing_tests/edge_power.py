import typing as t
import time
import json
from collections import OrderedDict

from pandas import DataFrame

import pandas as pd


from celery import Task, current_task

from celery_worker import celeryapp
from .post_processing_task import PostProcessingBaseTask

class EdgePowerTask(PostProcessingBaseTask):
    test = "Edge Power"

    def run_post_processing(self, df: pd.DataFrame) -> t.OrderedDict[str,
                                                                     pd.DataFrame]:
        print(current_task.config.RESULTS_FOLDER)
        return OrderedDict([("Fake Sheet Name", df)])



@celeryapp.task(name='edge_power')
def edge_power_task(*args, **kwargs):
    print("POWER TASK RECEIVED!")
    result = EdgePowerTask().run(*args, **kwargs)
    return result