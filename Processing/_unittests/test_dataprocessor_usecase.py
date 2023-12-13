import pandas as pd

from Processing.TestDataProcessors._unittests.unittest_testcase_helper import DataProcessorTestCaseHelper
from Processing.dataprocessor_usecase import DataProcessor


class DataProcessorTestCase(DataProcessorTestCaseHelper):

    def setUp(self) -> None:
        super(DataProcessorTestCase, self).setUp()
        self.processor = DataProcessor()

    def test_waveform_names(self):
        names = self.processor._waveform_names(dataframe=self.maintoaux_df)
        # print(names)
        self.assertIsInstance(names, list)
        self.assertListEqual(names, ['12V_EXT', '12V_EXT_Current', 'PVNN', 'SSD_V0P9', 'SSD_V1P2', 'SSD_V2P5',
                                     'V3P3', 'V5P0'])

    def test_product_name(self):
        name = self.processor._product_name(dataframe=self.maintoaux_df)
        # print(name)
        self.assertIsInstance(name, str)
        self.assertEqual(name, "Clara Peak")

    def test_query_testpoints(self):
        query_result = self.processor._query_testpoints(product="Clara Peak", testpoint_list=["12V_EXT"])
        print(query_result)
        self.assertIsInstance(query_result, pd.DataFrame)
        self.assertEqual(query_result.shape[0], 1)  # only 1 row

        query_result = self.processor._query_testpoints(product="Clara Peak")
        print(query_result)
        self.assertIsInstance(query_result, pd.DataFrame)
        self.assertGreater(query_result.shape[0], 1)  # only 1 rowe
