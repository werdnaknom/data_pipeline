import typing as t
import json
import datetime as dt
from collections import OrderedDict

from celery import current_task

import pandas as pd

from celery_worker import celeryapp
from .post_processing_task import WaveformPostProcessingBaseTask

from app.UseCases.Automation_Tests_UseCases.load_profile import \
    LoadProfileUseCase, AutomationTestRequestObject

from app.Repository.repository import MongoRepository


class LoadProfileTask(WaveformPostProcessingBaseTask):
    _file_prefix = "LoadProfile"
    test = "Load Profile"

    def run_post_processing(self, df: pd.DataFrame, filter_by: str) \
            -> t.OrderedDict[str, pd.DataFrame]:
        req = AutomationTestRequestObject(df=df,
                                          filter_by=filter_by)
        uc = LoadProfileUseCase(repo=MongoRepository())
        result = uc.execute(request_object=req)

        return result.value


@celeryapp.task(name='load_profile')
def load_profile_task(*args, **kwargs):
    print("LOAD PROFILE TASK RECEIVED!")
    result = LoadProfileTask().run(*args, **kwargs)
    return result


'''
class LoadProfileTask(Task):

    def run(self, *args, **kwargs):
        request_str = kwargs["request"]
        request_dict = json.loads(request_str)
        data_path = request_dict["data_file_path"]
        config_path = request_dict["user_input_file_path"]
        # data_path = kwargs["data_file_path"]
        # config_path = kwargs["user_input_file_path"]

        current_task.update_state(state="PROGRESS",
                                  meta={"current": 1, 'total': 10,
                                        "status": "Cleaning Input Data..."})
        cleaned_req = cleanup.apply_async(kwargs={"config_path": config_path,
                                                  "data_path": data_path})
        cleaned_df_json = cleaned_req.get()

        current_task.update_state(state="PROGRESS",
                                  meta={"current": 4, 'total': 10,
                                        "status": "Updating Data Repository..."})

        entity_df = update_mongo.apply_async(kwargs={"df_json":
                                                         cleaned_df_json})
        final_df_json = entity_df.get()
        current_task.update_state(state="PROGRESS",
                                  meta={"current": 7, 'total': 10,
                                        "status": "Post Processing..."})

        return {'current': 100, 'total': 100, 'status': 'Task completed!',
                'result': {
                    "Fake Data": final_df_json},
                'filename': f"LoadProfile_{dt.datetime.now()}"}
'''

'''
@celeryapp.task(bind=True, name='load_profile_update_tasks')
def load_profile_update_tasks(self, config_path: str, data_path: str):
    self.update_state(state="PROGRESS",
                      meta={"current": 1, 'total': 20,
                            "status": config_path})
    time.sleep(4)
    self.update_state(state="PROGRESS",
                      meta={"current": 10, 'total': 20,
                            "status": data_path})
    time.sleep(4)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@celeryapp.task(name='load_profile_task_group')
def load_profile_task_group():
    task_group = group(fake_task.s(), fake_task.s(), fake_task.s(),
                       fake_task.s())
    tg = task_group()
    task_ids = [t.id for t in tg.children]
    return task_ids


@celeryapp.task(bind=True)
def fake_task(self):
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter',
            'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message})
        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}
'''
