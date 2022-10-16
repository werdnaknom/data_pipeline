import typing as t
import logging
from pathlib import Path
import os
import pandas as pd
import random
import string

from celery import Task, current_task
from app import globalConfig

logger = logging.getLogger(__name__)


class CeleryTaskBaseClass(Task):
    _file_prefix = "BaseClass"

    def celery_update_state(self, state: str, current: int, total: int,
                            status: str, subtasks: t.List[str] = None) -> bool:
        if subtasks is None:
            subtasks = []
        task = current_task
        if isinstance(task, type(None)):
            # Celery is not alive
            return False
        else:
            current_task.update_state(state=state,
                                      meta={"current": current, 'total': total,
                                            "status": status, "subtasks":
                                                subtasks})
            # Celery is Alive
            return True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.exception(str(einfo))
        logger.debug(
            "Task_id {} failed, Arguments are {}".format(task_id, args))

        # current_datetime = datetime.now()
        # datetime_str = str(current_datetime)
        # error_details_api_url = "{}celery-error-log/?datetime={}".format(current_config.SERVER_DOMAIN, datetime_str.replace(" ", '%20'))
        # error_message = "*Attention:*`Task Failed`\n>*Task Name:* {}\n>*Task_id:* {}\n>*Error Details api url:* {}\n".format(self.name, task_id, error_details_api_url)
        # CeleryErrorLog(task_id=task_id, args=str(args), datetime=current_datetime, kwargs=str(kwargs), error=str(einfo), is_active=True).save()


    @classmethod
    def file_prefix(cls):
        return cls._file_prefix


    @classmethod
    def pickle_load_str_df(cls, pickle_str: str) -> pd.DataFrame:
        p = Path(pickle_str)
        assert p.exists(), f"Path {p.resolve} did not exists!"
        df = cls.pickle_load_df(pickle_path=p)
        return df

    @classmethod
    def pickle_load_df(cls, pickle_path: Path) -> pd.DataFrame:
        df = pd.read_pickle(pickle_path)
        return df

    @classmethod
    def temp_filename(cls, length=20, suffix=".pkl") -> str:
        filename = ''.join(random.sample(string.ascii_letters, length))
        if not suffix[0] == ".":
            suffix = "." + suffix
        filename = filename + suffix
        return filename

    @classmethod
    def df_to_pickle(cls, df: pd.DataFrame, base_path: Path = None) -> Path:
        if base_path is None:
            base_path = globalConfig.CELERY_TEMP_FOLDER
            #base_path = r"C:\Users\ammonk\OneDrive - Intel " \
            #              r"Corporation\Desktop\Test_Folder\fake_uploads" \
            #              r"\CeleryTemp"
        filename = cls.temp_filename(length=20, suffix=".pkl")
        filename = f"{cls.file_prefix()}_{filename}"
        filepath = Path(base_path).joinpath(filename)
        pkl_path = cls._df_to_pickle(df=df, filepath=filepath)
        return pkl_path

    @classmethod
    def _df_to_pickle(cls, df: pd.DataFrame, filepath: Path) -> Path:
        pd.to_pickle(df, filepath)
        return filepath

    @classmethod
    def path_to_str(cls, path:Path) -> str:
        str_path = os.fspath(path)
        return str_path