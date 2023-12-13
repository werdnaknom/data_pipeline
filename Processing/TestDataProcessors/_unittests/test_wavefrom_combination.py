from unittest import TestCase
from unittest_testcase_helper import DataProcessorTestCaseHelper
from Processing.RepoProcessors import SequencingRepositoryProcessor
from pathlib import Path
import pandas as pd


class TestCaseWaveformCombination(DataProcessorTestCaseHelper):

    def test_case(self):
        print(self.maintoaux_df)
