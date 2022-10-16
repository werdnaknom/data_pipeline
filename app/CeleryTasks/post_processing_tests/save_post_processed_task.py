import typing as t
import time
import json
from pathlib import Path
from collections import OrderedDict

import pandas as pd

from celery import Task, current_task
import pickle

from celery_worker import celeryapp
from .post_processing_task import PostProcessingBaseTask
from app.Repository.repository import MongoRepository

SAVE_LOCATION = Path(
    r'C:\Users\ammonk\OneDrive - Intel Corporation\Desktop\Test_Folder\fake_uploads')


class SaveTask(PostProcessingBaseTask):
    test = "SaveData Task"

    def run_post_processing(self, df: pd.DataFrame) -> t.OrderedDict[str,
                                                                     pd.DataFrame]:
        filename = "post_processed_AuxToMain.pkl"
        df.to_pickle(path=SAVE_LOCATION.joinpath(filename))
        mongo = MongoRepository()

        for i, row in df.iterrows():
            wf = mongo.find_waveform_by_id(waveform_id=row["waveform_id"])
            file_path = SAVE_LOCATION.joinpath(
                "post_processed_entities").joinpath("AuxToMain_Waveforms")
            filename = f"{row['waveform_id']}.pkl"
            save_location = file_path.joinpath(filename)
            with open(save_location, "wb") as f:
                pickle.dump(wf, f)
            print(wf)
        return OrderedDict([("Sheet1", df)])


@celeryapp.task(name='save_data')
def save_data_task(*args, **kwargs):
    print("\n"*5)
    print("SAVE DATA WHOOHOO")
    print("\n"*5)
    result = SaveTask().run(*args, **kwargs)
    return result
