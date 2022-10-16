import typing as t
import time
import json
from collections import OrderedDict

import pandas as pd

from celery import Task, current_task

from celery_worker import celeryapp
from .post_processing_task import WaveformPostProcessingBaseTask

class PowerOnTimeTask(WaveformPostProcessingBaseTask):
    test = "Power-on Time"

    def run_post_processing(self, df: pd.DataFrame) -> t.OrderedDict[str,
                                                                     pd.DataFrame]:
        return OrderedDict([("Fake Sheet Name", df)])


@celeryapp.task(name='power-on_time')
def power_on_time_task(*args, **kwargs):
    print("POWER-ON TIME TASK RECEIVED!")
    result = PowerOnTimeTask().run(*args, **kwargs)
    return result
