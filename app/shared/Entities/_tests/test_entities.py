import typing as t
import logging
import sys
from unittest import TestCase, mock
import datetime
import pickle

from pandas import Series
import numpy as np
import matplotlib.pyplot as plt

from basicTestCase.basic_test_case import BasicTestCase

from app.shared.Entities.entities import WaveformEntity
from app.shared.Entities import RunidEntity, WaveformCaptureEntity
from app.shared.Entities._tests.test_helper import dataframe_row


class WaveformEntityTestCase(BasicTestCase):
    logger_name = "WaveformEntity_TestLogger"

    def _setUp(self) -> None:
        self.df_row = dataframe_row
        self.wfs = self._helper_load_waveforms()

    def test_waveform_steady_state(self):
        expected_results = [101, 0, 101, 101, 101, 101, 101, 101]
        for wf, expected in zip(self.wfs, expected_results):
            x = wf.steady_state_index()
            self.logger.debug(f"{wf.testpoint} expected result is {expected} "
                              f"and was {x}")
            self.assertEqual(x, expected)


class RunidEntityTestCase(BasicTestCase):
    logger_name = "WaveformEntity_TestLogger"

    def _setUp(self) -> None:
        self.df_row = dataframe_row

    def test_from_dataframe_row(self):
        expected_result = {'runid': 2, 'status': {'status': 'Aborted',
                                                  'time': '10/4/2019 10:32',
                                                  'info': 'Test was aborted by user after 1 Hours 30 Minutes 11 Seconds',
                                                  'runtime_total_seconds': 5411,
                                                  'runtime_seconds': 11,
                                                  'runtime_hours': 1,
                                                  'runtime_minutes': 30,
                                                  '_id': None,
                                                  'modified_date': datetime.datetime(
                                                      2020, 9, 15, 20, 24, 10,
                                                      885305),
                                                  'created_date': datetime.datetime(
                                                      2020, 9, 15, 20, 24, 10,
                                                      885305)},
                           'system_info': {'probes': [],
                                           'scope_serial_number': None,
                                           'power_supply_serial_number': None,
                                           'ats_version': '', '_id': None,
                                           'modified_date': datetime.datetime(
                                               2020, 9, 15, 20, 24, 10, 885305),
                                           'created_date': datetime.datetime(
                                               2020, 9, 15, 20, 24, 10,
                                               885305)},
                           'testrun': {'dut': 'Mentor Harbor',
                                       'pba': 'K31123-001', 'rework': '0',
                                       'serial_number': ' A6081C',
                                       'technician': 'Tony Strojan',
                                       'test_station': 'lno-test11',
                                       'configuration': 'Config 1',
                                       'board_id': 1955,
                                       'test_points': {'1': '12V_MAIN',
                                                       '2': '12V_MAIN CURRENT',
                                                       '3': '3P3V',
                                                       '4': '1P8V_VDDH',
                                                       '5': 'DVDD',
                                                       '6': '0P9V_AVDD_ETH',
                                                       '7': '0P9V_AVDD_PCIE',
                                                       '8': '1P1V_AVDDH'},
                                       '_id': None,
                                       'modified_date': datetime.datetime(2020,
                                                                          9, 15,
                                                                          20,
                                                                          24,
                                                                          10,
                                                                          885305),
                                       'created_date': datetime.datetime(2020,
                                                                         9, 15,
                                                                         20, 24,
                                                                         10,
                                                                         885305)},
                           'comments': {
                               'comments': {'Line0': 'Configuration #1'},
                               '_id': None,
                               'modified_date': datetime.datetime(2020, 9, 15,
                                                                  20, 24, 10,
                                                                  885305),
                               'created_date': datetime.datetime(2020, 9, 15,
                                                                 20, 24, 10,
                                                                 885305)},
                           '_type': 'RUNID', '_id': '2',
                           'modified_date': datetime.datetime(2020, 9, 15, 20,
                                                              24, 10, 850748),
                           'created_date': datetime.datetime(2020, 9, 15, 20,
                                                             24, 10, 850748)}

        runid = RunidEntity.from_dataframe_row(df_row=self.df_row)

        self.assertDictEqual(runid, expected_result)

    def test_to_result(self):
        expected_result = {'Runid': 2, 'Test Setup Comment': 'Configuration #1',
                           'Automation Status': 'Aborted',
                           'Test Configuraton': 'Config 1',
                           'Technician': 'Tony Strojan',
                           'Test Station': 'lno-test11'
                           }

        runid = RunidEntity.from_dataframe_row(df_row=self.df_row)

        result = runid.to_result()

        print(result)
        self.assertEqual(result, expected_result)


class DataCaptureTestCase(BasicTestCase):
    logger_name = "Capture_TestLogger"

    def _setUp(self) -> None:
        self.df_row = dataframe_row

    def test_to_result(self):
        expected_result = {
            'Capture': 1,
            'Temperature (C)': 25,
            '12V_MAIN Channel': 1,
            '12V_MAIN Setpoint (V)': 10.8,
            '12V_MAIN Slewrate (V/S)': 200,
            '12V_MAIN Group': 'Main',
            'PCIE 3.3V Main Channel': 2,
            'PCIE 3.3V Main Setpoint (V)': 3.3,
            'PCIE 3.3V Main Slewrate (V/S)': 1000,
            'PCIE 3.3V Main Group': 'Disabled',
            '3.3V_AUX Channel': 3,
            '3.3V_AUX Setpoint (V)': 3.3,
            '3.3V_AUX Slewrate (V/S)': 200,
            '3.3V_AUX Group': 'Aux',
            'None Channel': 4,
            'None Setpoint (V)': 0.02,
            'None Slewrate (V/S)': 1000,
            'None Group': 'Disabled'}

        e = WaveformCaptureEntity.from_dataframe_row(df_row=self.df_row)

        result = e.to_result()
        print(result)

        self.assertEqual(expected_result, result)
