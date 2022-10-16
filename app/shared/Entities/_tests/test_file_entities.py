import json
import typing as t
from unittest import TestCase, mock
import datetime
from collections import OrderedDict
import random
from pathlib import Path

from pandas import Series, DataFrame

from app.shared.Entities.file_entities import CommentsFileEntity, \
    StatusFileEntity, SystemInfoFileEntity, TestRunFileEntity, \
    CaptureEnvironmentFileEntity, ProbesFileEntity, PowerSupplyChannel, \
    CaptureSettingsEntity, DUTTrafficFileEntity, LPTrafficFileEntity, Port, \
    PowerCSVFileEntity, RunidPowerCSVFileEntity, CapturePowerCSVFileEntity
from app.shared.Entities._tests.test_helper import dataframe_row, ethagent_row
from basicTestCase.basic_test_case import BasicTestCase


class FileEntityTestCase(BasicTestCase):
    logger_name = 'FileEntityTestLogger'
    entity = None
    ROWFMT = None
    entity_keys = None

    def _setUp(self) -> None:
        self.location = r'\\npo\coos\LNO_Validation\Validation_Data\_data\ATS ' \
                        r'2.0\Mentor Harbor\K31123-003\RW00\BB063A\906\Tests\Aux ' \
                        r'To Main\2\CH1.bin'
        self.df_row = dataframe_row

    def _helper_to_result_tests(self, entity, expected_results: t.List[
        t.Tuple], row=dataframe_row):
        e = entity.from_dataframe_row(df_row=row)
        result = e.to_result()

        self.logger.debug(f"{entity.__name__} returned result: {result}")

        for r, e in zip(result.items(), expected_results):
            self.logger.debug(f"KEY: {r[0]} == {e[0]}")
            self.logger.debug(f"VALUE: {r[1]} == {e[1]}")
            self.assertEqual(r[0], e[0])
            self.assertEqual(r[1], e[1])

    def _test_from_dataframe_helper(self, entity):
        self.logger.debug(f"Testing Entity: {entity}\n")
        self.assertIsInstance(entity, self.entity)
        entity_keys = self.entity_keys
        row_keys = [f"{self.ROWFMT}{key}" for key in entity_keys]
        for e, row in zip(entity_keys, row_keys):
            entity_value = entity.__getattribute__(e)
            try:
                row_value = self.df_row[row]
                self.assertEqual(entity.__getattribute__(e), self.df_row[row])
            except KeyError:
                row_value = None
                self.logger.warning(f"\nKey[{row}] doesn't exist in dataframe "
                                    f"row!\n")

            self.logger.debug(f"Entity[{e}] --> {entity_value} <-- should "
                              f"equal Row[{row}] --> {row_value} <--")

    def _test_from_dict_helper(self, entity_dict: dict):
        e = self.entity.from_dict(adict=entity_dict)
        self.logger.debug(msg=f"Dict created Entity: {e}")
        self.assertIsInstance(e, self.entity)
        for key, value in entity_dict.items():
            entity_value = e.__getattribute__(key)
            self.logger.debug(f"Entity[{key}] --> {entity_value} <-- should "
                              f"equal dict[{key}] --> {value} <--")
            self.assertEqual(entity_value, value)
        return e

    def _test_to_dict_helper(self, entity, test_dict):
        self.logger.debug("\n" + "----" * 15)
        self.logger.debug(f"Starting {self.entity.__name__} "
                          f"to_dict Test")
        self.logger.debug("----" * 15 + "\n")

        edict = entity.to_dict()
        for key, value in test_dict.items():
            entity_value = edict[key]
            self.logger.debug(f"Entity[{key}] --> {entity_value} <-- should "
                              f"equal dict[{key}] --> {value} <--")
            self.assertEqual(entity_value, value)

        self.assertIsInstance(edict['created_date'], datetime.datetime)
        self.assertIsInstance(edict['modified_date'], datetime.datetime)

    def _test_from_dataframe_row(self):
        self.logger.debug("\n" + "----" * 15)
        self.logger.debug(f"Starting {self.entity.__name__} "
                          f"from_dataframe_row Test")
        self.logger.debug("----" * 15 + "\n")
        # SHOULD THE INPUT BE SELF OR SELF.DF_ROW??? HOW TO PROVE ENTITY?
        entity = self.entity.from_dataframe_row(df_row=self.df_row)
        self._test_from_dataframe_helper(entity=entity)

    def _test_from_dict(self, entity_dict):
        self.logger.debug("\n" + "----" * 15)
        self.logger.debug(f"Starting {self.entity.__name__} "
                          f"from_dict Test")
        self.logger.debug("----" * 15 + "\n")

        entity = self._test_from_dict_helper(entity_dict=entity_dict)
        return entity


class CommentFileTestCase(FileEntityTestCase):

    def test_to_result_real_row(self):
        e = CommentsFileEntity.from_dataframe_row(dataframe_row)
        result = e.to_result()

        self.logger.debug(f"Comment [To Result] = {result}")
        self.assertIsInstance(result, OrderedDict)
        for key, value in result.items():
            self.assertEqual(key, "Test Setup Comment")
            self.assertEqual(value, "Configuration #1")

    def test_to_result_fake_row(self):
        comment = "This is \n A Test \n Comment"
        row = Series({"comments": comment,
                      "Other Data": 12134})
        e = CommentsFileEntity.from_dataframe_row(df_row=row)
        result = e.to_result()

        self.logger.debug(f"Comment [To Result] = {result}")
        self.assertIsInstance(result, OrderedDict)
        for key, value in result.items():
            self.assertEqual(key, "Test Setup Comment")
            self.assertEqual(value, comment.replace("\n", ""))

    def test_from_dataframe_row(self):
        row = Series({"comments": "This is \n A Test \n Comment",
                      "Other Data": 12134})

        e = CommentsFileEntity.from_dataframe_row(df_row=row)
        self.logger.debug(msg=f"Comments File Entity: {e}")

        self.assertIsInstance(e.comments, dict)
        self.assertDictEqual(e.comments,
                             {"Line0": 'This is ', "Line1": ' A Test ',
                              "Line2": ' Comment'})
        self.assertEqual(e._id, None)
        self.assertIsInstance(e.created_date, datetime.datetime)
        self.assertIsInstance(e.modified_date, datetime.datetime)

    def test_from_empty_dataframe_comments(self):
        row = Series({"comments": "",
                      "Other Data": 12134})

        e = CommentsFileEntity.from_dataframe_row(df_row=row)
        self.logger.debug(msg=f"Comments File Entity: {e}")

        self.assertIsInstance(e.comments, dict)
        self.assertDictEqual(e.comments, {})
        self.assertEqual(e._id, None)
        self.assertIsInstance(e.created_date, datetime.datetime)
        self.assertIsInstance(e.modified_date, datetime.datetime)

    def test_from_to_dict(self):
        comments_dict = {0: 'This is ', 1: ' A Test ', 2: ' Comment'}
        _id_test = "This is an ID"
        d = {"comments": comments_dict,
             "_id": _id_test}
        e = CommentsFileEntity.from_dict(adict=d)
        self.logger.debug(e)

        self.assertDictEqual(e.comments, comments_dict)
        self.assertEqual(e._id, _id_test)

        result_dict = e.to_dict()
        self.logger.debug(result_dict)

        d['created_date'] = result_dict['created_date']
        d['modified_date'] = result_dict['modified_date']

        self.assertDictEqual(result_dict, d)


class StatusFileEntityTestCase(FileEntityTestCase):
    entity = StatusFileEntity
    entity_keys = ["status", "time", "info", "runtime_total_seconds",
                   "runtime_seconds", "runtime_hours", "runtime_minutes"]
    ROWFMT = "status_json_"

    def test_status_to_result(self):
        row = dataframe_row

        e = StatusFileEntity.from_dataframe_row(row)

        result = e.to_result()
        self.logger.debug(f"status result: {result}")
        for key, value in result.items():
            self.assertEqual(key, "Automation Status")
            self.assertEqual(value, "Aborted")

    def test_from_dataframe_row(self):
        self._test_from_dataframe_row()

    def test_from_dict(self):
        entity_dict = {"status": 'Aborted',
                       "time": '10/4/2019 10:32',
                       "info": 'Test was aborted by user after 1 Hours 30 Minutes 11 Seconds',
                       "runtime_total_seconds": 5411, "runtime_seconds": 11,
                       "runtime_hours": 1, "runtime_minutes": 30, "_id":
                           "This is an ID"}
        e = self._test_from_dict(entity_dict=entity_dict)

        self._test_to_dict_helper(entity=e, test_dict=entity_dict)


class SystemInfoEntityTestCase(FileEntityTestCase):
    entity = SystemInfoFileEntity
    entity_keys = ["scope_serial_number", "power_supply_serial_number",
                   "ats_version"]
    ROWFMT = entity.get_row_format()

    def test_from_dataframe_row(self):
        self._test_from_dataframe_row()

    def test_from_dict(self):
        entity_dict = {"scope_serial_number": "B12354",
                       "power_supply_serial_number": "C12345",
                       "ats_version": "Z12345"}
        e = self._test_from_dict(entity_dict=entity_dict)

        self._test_to_dict_helper(entity=e, test_dict=entity_dict)

    def test_to_result(self):
        self._helper_to_result_tests(SystemInfoFileEntity,
                                     expected_results=[("ATS Version", "")])

    def test_fake_to_result(self):
        entity_dict = {"system_info_json_scope_serial_number": "B12354",
                       "system_info_json_power_supply_serial_number": "C12345",
                       "system_info_json_ats_version": "Z12345"}
        row = Series(entity_dict)

        self._helper_to_result_tests(SystemInfoFileEntity,
                                     expected_results=[("ATS Version",
                                                        "Z12345")],
                                     row=row)


class TestRunFileEntityTestCase(FileEntityTestCase):
    entity = TestRunFileEntity
    entity_keys = ["dut", "pba", "rework", "serial_number", "technician",
                   "test_station", "test_points", "board_id", "configuration"]
    ROWFMT = entity.get_row_format()

    def test_from_dataframe_row(self):
        self._test_from_dataframe_row()

    def test_from_dict(self):
        entity_dict = {"dut": "Mentor Harbor", "pba": "K31123-003",
                       "rework": "RW00", "serial_number": "BB063A",
                       "technician": "ON", "test_station": "lno-test5",
                       "test_points": {'1': '12V_MAIN', '2': '12V_MAIN CURRENT',
                                       '3': '3P3V', '4': '1P8V_VDDH',
                                       '5': 'DVDD', '6': '0P9V_AVDD_ETH',
                                       '7': '0P9V_AVDD_PCIE',
                                       '8': '1P1V_AVDDH'},
                       "board_id": 2186, "configuration": "Config1"}
        e = self._test_from_dict(entity_dict=entity_dict)

        self._test_to_dict_helper(entity=e, test_dict=entity_dict)

    def test_serial_number_as_number(self):
        entity_dict = {"dut": "Mentor Harbor", "pba": "K31123-003",
                       "rework": "RW00", "serial_number": 120635,
                       "technician": "ON", "test_station": "lno-test5",
                       "test_points": {'1': '12V_MAIN', '2': '12V_MAIN CURRENT',
                                       '3': '3P3V', '4': '1P8V_VDDH',
                                       '5': 'DVDD', '6': '0P9V_AVDD_ETH',
                                       '7': '0P9V_AVDD_PCIE',
                                       '8': '1P1V_AVDDH'},
                       "board_id": 2186, "configuration": "Config1"}
        e = TestRunFileEntity.from_dict(adict=entity_dict)
        #e = self._test_from_dict(entity_dict=entity_dict)

        self.assertIsInstance(e.serial_number, str)

        entity_dict["serial_number"] = "120635"

        self._test_to_dict_helper(entity=e, test_dict=entity_dict)

    def test_to_result(self):
        self._helper_to_result_tests(TestRunFileEntity,
                                     expected_results=[
                                         ("Test Configuraton", "Config 1"),
                                         ("Technician", "Tony Strojan"),
                                         ("Test Station", "lno-test11")
                                     ])


class CaptureFileEntityTestCase(FileEntityTestCase):
    entity = CaptureSettingsEntity
    entity_keys = ["initial_x", "x_increment", "compress", "waveform_names"]

    ROWFMT = entity.get_row_format()

    def test_from_dataframe_row(self):
        self._test_from_dataframe_row()

    def test_from_dict(self):
        entity_dict = {"initial_x": 0.123,
                       "x_increment": 0.435,
                       "compress": True,
                       "waveform_names": ["waveform", "Names"]}
        e = self._test_from_dict(entity_dict=entity_dict)

        self._test_to_dict_helper(entity=e, test_dict=entity_dict)

    def test_to_result(self):
        expected_result = []

        self._helper_to_result_tests(CaptureSettingsEntity,
                                     expected_results=expected_result)


class CaptureSettingsFileEntityTestCase(FileEntityTestCase):
    entity = CaptureEnvironmentFileEntity
    entity_keys = ["chamber_setpoint", "dut_on", "power_supply_channels"]

    ROWFMT = entity.get_row_format()

    def test_from_dataframe_row(self):
        self._test_from_dataframe_row()

    def test_from_empty_dict(self):
        entity_dict = {}
        with self.assertRaises(AssertionError):
            e = self._test_from_dict(entity_dict=entity_dict)
            self._test_to_dict_helper(entity=e, test_dict=entity_dict)

    def test_from_dict(self):
        entity_dict = {"chamber_setpoint": 25,
                       "dut_on": True}

        e = self._test_from_dict(entity_dict=entity_dict)
        self._test_to_dict_helper(entity=e, test_dict=entity_dict)

    def test_create_power_supply_channels(self):
        keys = {key for key in self.df_row.keys() if
                CaptureEnvironmentFileEntity.get_row_format() in key}

        channels = CaptureEnvironmentFileEntity.create_power_supply_channels(
            keys=keys,
            df_row=self.df_row)

        print(channels)

    def test_to_result(self):
        expected_result = [('Temperature (C)', 25),
                           ("12V_MAIN Channel", 1),
                           ('12V_MAIN Setpoint (V)', 10.8),
                           ('12V_MAIN Slewrate (V/S)', 200),
                           ('12V_MAIN Group', 'Main'),
                           ("PCIE 3.3V Main Channel", 2),
                           ('PCIE 3.3V Main Setpoint (V)', 3.3),
                           ('PCIE 3.3V Main Slewrate (V/S)', 1000),
                           ('PCIE 3.3V Main Group', 'Disabled'),
                           ("3.3V_AUX Channel", 3),
                           ('3.3V_AUX Setpoint (V)', 3.3),
                           ('3.3V_AUX Slewrate (V/S)', 200),
                           ('3.3V_AUX Group', 'Aux')]

        self._helper_to_result_tests(CaptureEnvironmentFileEntity,
                                     expected_results=expected_result)


class TrafficFileTests(BasicTestCase):
    entity = None
    entity_keys = []
    ROWFMT = None

    def _setUp(self):
        self.df_row = ethagent_row

    def _test_from_dataframe_row(self):
        self.logger.debug("\n" + "----" * 15)
        self.logger.debug(f"Starting {self.entity.__name__} "
                          f"from_dataframe_row Test")
        self.logger.debug("----" * 15 + "\n")

        entity = self.entity.from_dataframe_row(df_row=self.df_row)
        # self._test_from_dataframe_helper(entity=entity)
        return entity


class DUTTrafficFileEntityTestCase(TrafficFileTests):
    entity = DUTTrafficFileEntity

    def test_from_dataframe_row(self):
        result_entity = self._test_from_dataframe_row()
        self.logger.debug(f"Testing Entity: {result_entity}\n")

        self.assertIsInstance(result_entity, DUTTrafficFileEntity)
        self.assertEqual(2, len(result_entity.ports))
        for port in result_entity.ports:
            self.assertIsInstance(port, Port)

    def test_from_dict(self):
        self.fail()

    def test_to_result(self):
        self.fail()


class LPTrafficFileEntityTestCase(TrafficFileTests):
    entity = LPTrafficFileEntity

    def test_from_dataframe_row(self):
        result_entity = self._test_from_dataframe_row()
        self.logger.debug(f"Testing Entity: {result_entity}\n")

        self.assertIsInstance(result_entity, LPTrafficFileEntity)
        self.assertEqual(2, len(result_entity.ports))
        for port in result_entity.ports:
            self.assertIsInstance(port, Port)


class _PowerCSVFileEntityTestCase(FileEntityTestCase):
    entity = CapturePowerCSVFileEntity
    depth = None
    entity_keys = []
    ROWFMT = []  # entity.get_row_format()

    def power_test_find_keys_from_row(self):
        row, expected_num_results = self._generate_fake_filepaths()
        self.logger.debug(f"expected number of results: {expected_num_results}")
        keys = self.entity._find_keys_from_row(df_row=row)

        self.logger.debug(f"Function returned: {keys}")

        self.assertIsInstance(keys, tuple)

        self.assertEqual(expected_num_results, len(keys[0]))

        result_keys = keys[0]
        self.assertIn(f"file_{self.depth}_power.csv", result_keys)
        self.assertIn(f"file_{self.depth}_power (1).csv", result_keys)
        self.assertIn(f"file_{self.depth}_power.json",
                      keys[1].keys())  # result_keys)

    def _generate_fake_filepaths(self):
        row = self.df_row
        for r in range(2, random.randrange(3, stop=15)):
            row[f"file_{self.depth}_power ({r}).csv"] = f"Power{r}.csv"

        return row, r + 1  # only +1 because range starts at 0

    def power_test__extract_power_csv_list(self):
        row, expected_num_results = self._generate_fake_filepaths()
        self.logger.debug(f"expected number of results: {expected_num_results}")

        power_list = self.entity._extract_power_csv_list(df_row=row)

        self.assertIsInstance(power_list, list)
        for power_csv in power_list:
            self.assertIsInstance(power_csv, Path)
            self.assertEqual(power_csv.suffix, ".csv")
            self.assertIn("power", power_csv.name.lower())  # ADDED .lower()

        self.assertEqual(expected_num_results, len(power_list))

    def power_test__extract_power_json(self):
        expected_result = Path(self.df_row[f"file_{self.depth}_power.json"])
        json_path = self.entity._extract_power_json(df_row=self.df_row)

        self.logger.debug(f"Function returned: {json_path}")

        self.assertEqual(expected_result, json_path)

    def power_test__power_header_meta_type(self):

        power_path = Path(r"\\npo\coos\LNO_Validation\Validation_Data\_data"
                          r"\ATS "
                          r"2.0\Mentor Harbor\M19197-001\00\895866\1194\Tests\EthAgent\3\power.json")
        expected_headers = ['3.3_AUX Power', 'Temperature Setpoint',
                            '12V_MAIN Current', 'Total Power',
                            '3.3_AUX Volts Setpoint', '12V_MAIN Volts Setpoint',
                            '3.3_AUX Current', '12V_MAIN Slew', '3.3_AUX Slew',
                            '3.3_AUX State', '12V_MAIN Power', '12V_MAIN State',
                            'Time', '3.3_AUX Volts', 'Temperature',
                            '12V_MAIN Volts']
        expected_meta = ""
        expected_type = ""

        header, meta, type = self.entity._power_header_meta_type(
            header_json_path=power_path)

        for result in [header, meta, type]:
            self.assertIsInstance(result, list)
            self.assertEqual(len(expected_headers), len(result))

        for index, value in enumerate(header):
            self.assertIn(value, expected_headers)
            # self.assertEqual(expected_headers[index], value)

        for value in meta:
            self.assertEqual("", value)

        for value in type:
            self.assertEqual("", value)

    # def mock_read(self, i, headers):
    #    return DataFrame([[i for _ in range(2)] for _ in range(len(headers))],
    #                     columns=headers)

    def power_test_create_power_df(self):
        expected_headers = ['Time', 'Temperature Setpoint', 'Temperature',
                            '12V_MAIN Volts Setpoint', '12V_MAIN Volts',
                            '12V_MAIN Current', '12V_MAIN Power',
                            '12V_MAIN Slew', '12V_MAIN State',
                            '3.3_AUX Volts Setpoint', '3.3_AUX Volts',
                            '3.3_AUX Current', '3.3_AUX Power', '3.3_AUX Slew',
                            '3.3_AUX State', 'Total Power']

        df = self.entity._create_power_df(csv_list=[
            Path(
                r"\\npo\coos\LNO_Validation\Validation_Data\_data\ATS 2.0\Mentor "
                r"Harbor\M19197-001\00\895866\1194\Tests\EthAgent\3\power.csv"),
            Path(
                r"\\npo\coos\LNO_Validation\Validation_Data\_data\ATS 2.0\Mentor "
                r"Harbor\M19197-001\00\895866\1194\Tests\EthAgent\4\power.csv")
        ], json_header_file=Path(
            r"\\npo\coos\LNO_Validation\Validation_Data\_data\ATS 2.0\Mentor "
            r"Harbor\M19197-001\00\895866\1194\Tests\EthAgent\3\power.json"))

        self.logger.debug(f"Function returned df of size: {df.shape}")
        self.logger.debug(f"{df.head()}")

        self.assertIsInstance(df, DataFrame)
        self.assertListEqual(df.columns.tolist(),
                             expected_headers)  # CHANGED df.columns --> df.columns.tolist()

        self.assertEqual((468, 16), df.shape)

    def power_test_from_dict(self):
        '''
        This probably doesn't work because I don't know what the dataframe
        will look like or how to upload it to MONGODB! I'll figure that out
        while you're working on these....
        @return:
        '''

        entity_dict = {"folder_path": 'fake_path',
                       "dataframe": json.loads(DataFrame({"A": [1, 2, 5],
                                                          "B": [6, 7, 10]
                                                          }).to_json())}
        e = self._test_from_dict(entity_dict=entity_dict)

        self._test_to_dict_helper(entity=e, test_dict=entity_dict)


class CapturePowerCSVFileEntityTestCase(_PowerCSVFileEntityTestCase):
    entity = CapturePowerCSVFileEntity
    depth = "capture"
    entity_keys = []

    def test_find_keys_from_row(self):
        self.power_test_find_keys_from_row()

    def test__extract_power_csv_list(self):
        self.power_test__extract_power_csv_list()

    def test__extract_power_json(self):
        self.power_test__extract_power_json()

    def test_from_dataframe_row(self):
        self._test_from_dataframe_row()

    def test_from_dict(self):
        '''
        This probably doesn't work because I don't know what the dataframe
        will look like or how to upload it to MONGODB! I'll figure that out
        while you're working on these....
        @return:
        '''
        self.power_test_from_dict()
        self.fail("You can ignore this")
        # I will fail this if I want to use it in the method below this one

    def test__power_header_meta_type(self):  # DONE SORTA
        self.power_test__power_header_meta_type()

    def test_create_power_df(self):  # DONE
        self.power_test_create_power_df()


class RunidPowerCSVFileEntityTestCase(_PowerCSVFileEntityTestCase):
    entity = RunidPowerCSVFileEntity
    depth = "runid"
    entity_keys = []

    def test_find_keys_from_row(self):
        self.power_test_find_keys_from_row()

    def test__extract_power_csv_list(self):
        self.power_test__extract_power_csv_list()

    def test__extract_power_json(self):
        self.power_test__extract_power_json()

    def test_from_dataframe_row(self):
        self._test_from_dataframe_row()

    def test_from_dict(self):
        '''
        This probably doesn't work because I don't know what the dataframe
        will look like or how to upload it to MONGODB! I'll figure that out
        while you're working on these....
        @return:
        '''
        self.power_test_from_dict()
        self.fail("You can ignore this")

    def test__power_header_meta_type(self):
        self.power_test__power_header_meta_type()

    def test_create_power_df(self):
        self.power_test_create_power_df()
