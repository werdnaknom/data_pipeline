import typing as t
from pathlib import Path

import pandas as pd

from app.UseCases.Automation_Test_Post_Processing._tests \
    .IFailedAtOnePointBaseCase import IFailedAtOncePointBaseCase

from app.UseCases.Automation_Tests_UseCases.automation_test_usecase import \
    AutomationTestRequestObject

from app.UseCases.Automation_Tests_UseCases.ber import BitErrorRatioUseCase

from app.Repository.repository import Repository, MongoRepository


class EthAgentBitErrorRatioAlbanyFlatKulim(IFailedAtOncePointBaseCase):
    '''
    This data was created by Steve and did not show RX Errors, even when RX
    errors were occuring.

    There are 4 cases:
        - CASE 1:  LP Errors are reported as the "Rx Errors"
    '''
    BASE_DIRECTORY = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's Code\unit_test_data\IFailedAtOnePoint\CampbellFlat_EthAgent_PanicBER"
    AUTOMATION_TEST_DATAFOLDER = "EthAgent"
    DEFAULT_FILTERBY = "datacapture"
    PLOT_FIELDS = []
    EXPECTED_SHEETS = ["BitErrorRatio"]

    def _load_df(self, df_path: str):
        df = pd.read_excel(df_path, sheet_name="BitErrorRatio")

        return df

    def _setUp(self):
        self.uc = BitErrorRatioUseCase(repo=MongoRepository())

    def test_dut_filter_CASE1(self):
        ''' Case 1 has no errors on either Tx or Rx for the DUT and LP'''
        self.BASE_DIRECTORY = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's Code\unit_test_data\IFailedAtOnePoint\CampbellFlat_EthAgent_PanicBER\CASE1"
        df_path = self._test_filter(filter_by="dut")

        df = self._load_df(df_path=df_path)

        for header in ["DUT Rx Errors", "DUT Tx Errors", "LP Rx Errors",
                       "LP Tx Errors"]:
            col = df[header]
            unique_list = col.unique().tolist()
            self.assertListEqual([0], unique_list)

    def test_dut_filter_CASE2(self):
        ''' Case 2 has no errors on either Tx or Rx for the DUT and LP'''
        self.BASE_DIRECTORY = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's Code\unit_test_data\IFailedAtOnePoint\CampbellFlat_EthAgent_PanicBER\CASE2"
        df_path = self._test_filter(filter_by="dut")
        # {Port: {Capture: RX Errors}....
        dut_rx_dict = {
            0: {
                12: 18, 13: 58, 6: 1
            },
            3: {
                1: 9, 11: 41, 15: 4, 2: 1, 3: 54
            }}
        '''
        dutrx_errors = [(0, 18, 12), (0, 58, 13), (0, 1, 6),
                        (3, 9, 1), (3, 41, 11), (3, 4, 15), (3, 1, 2),
                        (3, 54, 3)]
        '''
        lp_rx_dict = {
            0: {
                12: 3, 13: 1694,
            },
            3: {
                1: 10, 10: 1, 11: 8, 13: 1, 15: 5, 2: 269852, 3: 79, 9: 10,
            }
        }
        '''
        lprx_errors_p0 = [(0, 3, 12), (0, 1694, 13),
                          (3, 10, 1), (3, 1, 10), (3, 8, 11), (3, 1, 13),
                          (3, 5, 15),
                          (3, 269852, 2), (3, 79, 3), (10, 9)]
        '''

        df = self._load_df(df_path=df_path)

        group = df.groupby(by=["Port", "Capture"])
        for (port, capture), gdf in group:
            dut_rx_errors = gdf['DUT Rx Errors'].values[0]
            dut_tx_errors = gdf['DUT Tx Errors'].values[0]
            lp_rx_errors = gdf['LP Rx Errors'].values[0]
            lp_tx_errors = gdf['LP Tx Errors'].values[0]
            dut_port_errors = dut_rx_dict.get(port, {}).get(capture, 0)
            lp_port_errors = lp_rx_dict.get(port, {}).get(capture, 0)

            print(f"{capture} -- PORT:{port} --> dut:{dut_rx_errors}, "
                  f"lp:{lp_rx_errors}")

            self.assertEqual(dut_port_errors, dut_rx_errors)
            self.assertEqual(lp_port_errors, lp_rx_errors)

            # There were no tx errors in this dataset
            self.assertEqual(0, dut_tx_errors)
            self.assertEqual(0, lp_tx_errors)

    def test_dut_filter_CASE3(self):
        self.BASE_DIRECTORY = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's " \
                              r"Code\unit_test_data\IFailedAtOnePoint\CampbellFlat_EthAgent_PanicBER\CASE3"
        # Run the actual test:
        df_path = self._test_filter(filter_by="dut")

        print(df_path)

    def test_dut_filter_CASE4(self):
        self.BASE_DIRECTORY = r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's " \
                              r"Code\unit_test_data\IFailedAtOnePoint\CampbellFlat_EthAgent_PanicBER\CASE4"
        # Run the actual test:
        df_path = self._test_filter(filter_by="dut")

        print(df_path)
