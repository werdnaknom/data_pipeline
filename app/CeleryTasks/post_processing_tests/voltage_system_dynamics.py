import typing as t

import pandas as pd

from celery_worker import celeryapp
from .post_processing_task import WaveformPostProcessingBaseTask
from app.UseCases.Automation_Tests_UseCases.voltage_system_dynamics import \
    VoltageSystemDynamicsUseCase, AutomationTestRequestObject

from app.Repository.repository import MongoRepository


class VoltageSystemDynamicsTask(WaveformPostProcessingBaseTask):
    test = "Voltage System Dynamics"

    def run_post_processing(self, df: pd.DataFrame, filter_by: str) \
            -> t.OrderedDict[str, pd.DataFrame]:
        '''

        @param df:
        @param filter_by:
        @return:
        '''

        req = AutomationTestRequestObject(df=df, filter_by=filter_by)

        uc = VoltageSystemDynamicsUseCase(repo=MongoRepository())
        result = uc.execute(request_object=req)

        return result.value


@celeryapp.task(name='voltage_system_dynamics')
def vsd_task(*args, **kwargs):
    result = VoltageSystemDynamicsTask().run(*args, **kwargs)
    return result
