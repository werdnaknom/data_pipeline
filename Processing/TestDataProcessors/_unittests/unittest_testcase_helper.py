import unittest
from Processing.RepoProcessors import SequencingRepositoryProcessor
from pathlib import Path
import pandas as pd

test_maintoaux_name = "clara-MainToAux_test_df.csv"


class DataProcessorTestCaseHelper(unittest.TestCase):

    def setUp(self) -> None:
        if Path(test_maintoaux_name).exists():
            self.maintoaux_df = pd.read_csv(test_maintoaux_name)
        else:
            self.maintoaux_df = self._build_maintoaux_testcase_csv()

    def _build_maintoaux_testcase_csv(self):
        repo = SequencingRepositoryProcessor()
        json_request = {
            "product": "Clara Peak",
            "runid_list": [6793],
            "test_category_list": ["Main To Aux"],
            "runid_status": ["Complete"],
        }
        result = repo.execute(json_request=json_request)

        print(result.dataframe)
        result.dataframe.to_csv("clara-MainToAux_test_df.csv")
        return result.dataframe
