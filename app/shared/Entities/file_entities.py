from __future__ import annotations

import datetime
import re
import typing as t
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from bson import ObjectId

from app.shared.Entities import Entity


@dataclass
class _FileEntityBase(Entity):
    _id: t.Optional[ObjectId] = None
    modified_date: datetime.datetime = field(
        default=datetime.datetime.utcnow(), repr=False, compare=False)
    created_date: datetime.datetime = field(
        default=datetime.datetime.utcnow(), repr=False, compare=False)

    @classmethod
    def get_row_format(cls, *args):
        raise NotImplementedError

    @classmethod
    def _find_keys_from_row(cls, df_row: pd.Series) -> dict:
        ''' Override for any more complex classes'''
        result = {}
        for key in df_row.keys():
            if cls.get_row_format() in key:
                rkey = cls.create_entity_key(key)
                result[rkey] = df_row[key]
        return result

    @classmethod
    def create_entity_key(cls, key):
        '''
        Override if entity_key is different!
        for instance System_Info has a probe list integrated
        '''
        return key.replace(cls.get_row_format(), "")

    @classmethod
    def from_dataframe_row(cls, df_row) -> _FileEntityBase:
        entity_dict = cls._find_keys_from_row(df_row)
        e = cls.from_dict(adict=entity_dict)
        return e


''' COMMENTS '''


@dataclass
class _CommentsBase():
    comments: dict


@dataclass
class CommentsFileEntity(_FileEntityBase, _CommentsBase):

    @classmethod
    def from_dataframe_row(cls, df_row) -> CommentsFileEntity:
        comment = str(df_row.comments)
        if comment:
            comments = {f"Line{i}": value for i, value in enumerate(
                comment.split(
                    "\n"))}
        else:
            comments = {}
        fe = CommentsFileEntity(comments=comments)
        return fe

    def to_result(self) -> OrderedDict:
        return OrderedDict([('Test Setup Comment',
                             "".join([value for value in
                                      self.comments.values()]))])


''' END COMMENTS '''

''' STATUS '''


@dataclass
class _StatusBase:
    status: str
    time: datetime.datetime
    info: str
    runtime_total_seconds: int
    runtime_seconds: int
    runtime_hours: int
    runtime_minutes: int


@dataclass
class StatusFileEntity(_FileEntityBase, _StatusBase):

    def __post_init__(self):
        self.runtime_total_seconds = int(self.runtime_total_seconds)
        self.runtime_seconds = int(self.runtime_seconds)
        self.runtime_hours = int(self.runtime_hours)
        self.runtime_minutes = int(self.runtime_minutes)

    @classmethod
    def get_row_format(cls):
        return "status_json_"

    def to_result(self) -> OrderedDict:
        return OrderedDict([
            ("Automation Status", self.status)
        ])


''' END STATUS'''
''' SYSTEMINFO PROBES'''


@dataclass
class _ProbesBase:
    channel: int
    type: str
    serial_number: str
    units: str
    cal_status: str


@dataclass
class ProbesFileEntity(_FileEntityBase, _ProbesBase):
    # TODO::
    pass

    def to_result(self) -> OrderedDict:
        return OrderedDict([
            ("Probe Type", self.type),
        ])


''' END SYSTEMINFO PROBES'''

''' SYSTEMINFO'''


@dataclass
class _SystemInfoBase:
    probes: list = field(default_factory=list)
    scope_serial_number: str = ""
    power_supply_serial_number: str = ""
    ats_version: str = ""


@dataclass
class SystemInfoFileEntity(_FileEntityBase, _SystemInfoBase, Entity):

    @classmethod
    def get_row_format(cls):
        return "system_info_json_"

    @classmethod
    def _find_keys_from_row(cls, df_row: pd.Series) -> dict:
        ''' Overrides parent method '''
        result = {}
        keys = [key for key in df_row.keys() if cls.get_row_format() in key]
        for key in keys:
            if "probe" in key:
                # TODO:: Add probe creation method
                continue
            rkey = cls.create_entity_key(key)
            result[rkey] = df_row[key]
        return result

    def to_result(self) -> OrderedDict:
        return OrderedDict([
            ("ATS Version", self.ats_version)
        ])


''' END SYSTEMINFO'''

''' TESTRUN '''


@dataclass
class _TestRunBase:
    dut: str
    pba: str
    rework: str
    serial_number: str
    technician: str
    test_station: str
    configuration: str
    board_id: int
    test_points: t.Dict[str] = field(default_factory=dict)


@dataclass
class TestRunFileEntity(_FileEntityBase, _TestRunBase, Entity):

    def __post_init__(self):
        self.rework = str(self.rework)
        self.configuration = str(self.configuration)
        self.serial_number = str(self.serial_number)
        self.board_id = self.verify_int_not_valueError(input=self.board_id)

    @classmethod
    def get_row_format(cls):
        return "testrun_json_"

    @classmethod
    def _find_keys_from_row(cls, df_row: pd.Series) -> dict:
        ''' Overrides parent method '''
        result = {"test_points": {}}
        keys = [key for key in df_row.keys() if cls.get_row_format() in key]
        for key in keys:
            if "test_point" in key:
                channel = key[-1]
                result['test_points'][channel] = df_row[key]
                continue
            rkey = cls.create_entity_key(key)
            result[rkey] = df_row[key]
        return result

    def to_result(self) -> OrderedDict:
        return OrderedDict([
            ("Test Configuraton", self.configuration),
            ("Technician", self.technician),
            ("Test Station", self.test_station),
        ])


''' END TESTRUN'''

''' WARNINGS '''


@dataclass()
class _WarningsBase:
    pass


@dataclass()
class WarningsFileEntity(_FileEntityBase, _WarningsBase, Entity):
    # TODO:: Complete warnings entity
    pass


''' END WARNINGS '''

''' CAPTURE '''


@dataclass
class _CaptureBase:
    initial_x: float
    x_increment: float
    compress: bool


@dataclass
class CaptureSettingsEntity(_FileEntityBase, _CaptureBase):
    waveform_names: t.List[str] = field(default_factory=list)

    def __post_init__(self):
        self.initial_x = float(self.initial_x)
        self.x_increment = float(self.x_increment)
        self.compress = bool(self.compress)

    @classmethod
    def get_row_format(cls):
        return "capture_json_"

    @classmethod
    def _find_keys_from_row(cls, df_row: pd.Series) -> dict:
        ''' Overrides parent method '''
        all_keys = {key for key in df_row.keys() if cls.get_row_format() in key}
        waveform_name_keys = set(key for key in all_keys if "names_" in key)

        # Get waveform names
        names = []
        for name_key in waveform_name_keys:
            names.append(df_row[name_key])
        entity_dict = {"waveform_names": names}

        # Get file specific keys

        file_keys = all_keys - waveform_name_keys
        for key in file_keys:
            rkey = cls.create_entity_key(key)
            entity_dict[rkey] = df_row[key]
        return entity_dict

    def to_result(self) -> OrderedDict:
        result_dict = OrderedDict()
        return result_dict


''' END CAPTURE '''

''' CAPTURE SETTINGS (AKA Temperature Power Settings) '''


@dataclass
class _PowerSupplyBase:
    channel: int
    channel_name: str
    channel_on: bool
    group: str
    voltage_setpoint: float
    slew_rate: int
    on_delay: float
    off_delay: float


@dataclass()
class PowerSupplyChannel(_FileEntityBase, _PowerSupplyBase):

    def __post_init__(self):
        self.channel = int(self.channel)
        self.channel_on = bool(self.channel_on)
        self.voltage_setpoint = float(self.voltage_setpoint)
        self.slew_rate = self.verify_int_not_valueError(self.slew_rate)
        self.on_delay = float(self.on_delay)
        self.off_delay = float(self.off_delay)

    @classmethod
    def get_row_format(cls):
        return "temperature_power_settings_json_power_supply_channels_"

    @classmethod
    def get_search_pattern(cls, channel):
        pattern = cls.get_row_format() + f".*_{channel}"
        compiled_pattern = re.compile(pattern=pattern)
        return compiled_pattern

    def to_result(self) -> OrderedDict:
        return OrderedDict([
            (f"{self.channel_name} Channel", self.channel),
            (f"{self.channel_name} Setpoint (V)", self.voltage_setpoint),
            (f"{self.channel_name} Slewrate (V/S)", self.slew_rate),
            (f"{self.channel_name} Group", self.group),
        ])


@dataclass
class _CaptureSettingsBase:
    chamber_setpoint: int
    dut_on: bool
    power_supply_channels: t.List[PowerSupplyChannel] = field(
        default_factory=list)


@dataclass
class CaptureEnvironmentFileEntity(_FileEntityBase, _CaptureSettingsBase,
                                   Entity):

    def __post_init__(self):
        self.chamber_setpoint = int(self.chamber_setpoint)
        if self.dut_on is "false":
            self.dut_on = False
        else:
            self.dut_on = True

    @classmethod
    def from_dict(cls, adict: dict) -> CaptureEnvironmentFileEntity:
        power_supply_chs = []
        assert "chamber_setpoint" in adict, f"CaptureEnvironmentFileEntity " \
                                            f"did not have correct input dictionary.  Should have contained 'chamber_setpoint', but only contained {adict}"
        assert "dut_on" in adict, f"CaptureEnvironmentFileEntity " \
                                  f"did not have correct input " \
                                  f"dictionary.  Should have contained " \
                                  f"'dut_on', but only contained {adict}"
        for power_ch in adict.get("power_supply_channels", []):
            ch_ent = PowerSupplyChannel.from_dict(power_ch)
            power_supply_chs.append(ch_ent)

        adict['power_supply_channels'] = power_supply_chs
        return cls(**adict)

    @classmethod
    def get_row_format(cls):
        return "temperature_power_settings_json_"

    @classmethod
    def _find_keys_from_row(cls, df_row: pd.Series) -> dict:
        ''' Overrides parent method '''
        result = {"power_supply_channels": []}
        keys = {key for key in df_row.keys() if cls.get_row_format() in key}
        power_supplies = {key for key in keys if "power_supply_channel" in key}
        setting_keys = keys - power_supplies
        power_supply_channels = cls.create_power_supply_channels(
            keys=power_supplies, df_row=df_row)
        result["power_supply_channels"] = [psc.to_dict()
                                           for psc in power_supply_channels]

        for key in setting_keys:
            rkey = cls.create_entity_key(key)
            result[rkey] = df_row[key]
        return result

    @classmethod
    def create_power_supply_channels(cls, keys: set, df_row: pd.Series) \
            -> t.List[PowerSupplyChannel]:
        result = []
        for x in range(1, 5):  # Loop over channels
            # print(x)
            channel_dict = {"channel": x,
                            "channel_name": "",
                            "group": "Disabled",
                            "voltage_setpoint": np.NaN,
                            "channel_on": False,
                            "on_delay": 0,
                            "off_delay": 0,
                            "slew_rate": np.NaN}
            regex_pattern = PowerSupplyChannel.get_search_pattern(channel=x)
            for key in keys:
                if regex_pattern.match(key):
                    rkey = key.replace(PowerSupplyChannel.get_row_format(),
                                       "")
                    # remove channel
                    fkey = rkey[:-2]

                    channel_dict[fkey] = df_row[key]

            # print(channel_dict)
            psc = PowerSupplyChannel(**channel_dict)
            result.append(psc)
        return result

    def to_result(self) -> OrderedDict:
        result_dict = OrderedDict([
            ("Temperature (C)", self.chamber_setpoint)
        ])
        for ch in self.power_supply_channels:
            # if ch.channel_on:
            #    result_dict.update(ch.to_result())
            result_dict.update(ch.to_result())

        return result_dict


@dataclass
class _PortBase():
    port: int
    bdf: str
    connection: str
    crc: int
    device_id: str
    etrack_id: str
    link: bool
    mac_addr: str
    device_name: str
    packet_size: int
    pattern: str
    remote_mac_addr: str
    rev_id: str
    rx_bps: int
    rx_errors: int
    rx_packets: int
    tx_bps: int
    tx_errors: int
    tx_packets: int
    slot: int
    speed: int
    state: str
    subsystem_id: str
    subsystem_vendor_id: str
    vendor_id: str
    target_speed: str


@dataclass
class Port(_FileEntityBase, _PortBase, Entity):

    def bits_sent(self) -> int:
        # Get packet size in bytes, multiply by 8 to get bits
        return (self.tx_packets * self.packet_size) * 8

    def convert_bps_to_Gbps(self, bps: int) -> float:
        Gbps = round(bps * 1E-9, 2)
        return Gbps

    def bits_recv(self, lp_pkt_size: int) -> int:
        '''
        Bits recv is harder -- We need to know the LP's packet size to
        calculate based on how many packets we've received.
        @return:
        '''
        bits = (self.rx_packets * lp_pkt_size) * 8  # Get packet size in bytes,
        # multiple by 8 to get bits
        return bits

    def errors(self) -> t.Tuple[int, int]:
        '''


        @return: RX Errors and RX Errors
        '''
        return self.rx_errors, self.tx_errors

    def to_result(self, suffix: str = None) -> OrderedDict:
        result = OrderedDict([
            ("Port", self.port),
            ("Link", self.link),
            ("ATS Link Speed", self.target_speed),
            ("Link Speed", self.speed),
            (f"{suffix} Tx (bps)", self.tx_bps),
            (f"{suffix} Rx (bps)", self.rx_bps),
            (f"{suffix} Tx (Gbps)", self.convert_bps_to_Gbps(self.tx_bps)),
            (f"{suffix} Rx (Gbps)", self.convert_bps_to_Gbps(self.rx_bps)),
            (f"{suffix} Tx Packets", self.tx_packets),
            (f"{suffix} Rx Packets", self.rx_packets),
            (f"{suffix} Tx Errors", self.tx_errors),
            (f"{suffix} Rx Errors", self.rx_errors)
        ])
        return result


@dataclass
class _TrafficBase:
    ports: t.List[Port]


@dataclass
class TrafficFileEntity(_FileEntityBase, _TrafficBase, Entity):
    device: str = ""

    @classmethod
    def from_dict(cls, adict: dict) -> CaptureEnvironmentFileEntity:
        ports = []
        for port in adict.get("ports", []):
            port_en = Port.from_dict(port)
            ports.append(port_en)

        adict['ports'] = ports
        return cls(**adict)

    @classmethod
    def get_row_format(cls):
        return f"{cls.device}_"

    @classmethod
    def _find_keys_from_row(cls, df_row: pd.Series) -> dict:
        ''' Overrides parent method '''
        # Matches anything that starts with {device}_ followed by any numbers
        # an ends with _json
        regex_pattern = f"\A{cls.device}_[0-9]*_json"

        result = {"ports": []}

        traffic_data = df_row.filter(regex=regex_pattern)
        ports = set(col.strip(cls.device + "_")[0] for col in
                    traffic_data.keys())
        for port in ports:
            port_regex = f"{cls.device}_{port}_json"
            port_data = traffic_data.filter(regex=port)
            port = int(port)
            crc = cls.verify_int_not_valueError(
                port_data.get(f"{port_regex}_slot_crc"))
            pkt_size = cls.verify_int_not_valueError(
                port_data.get(f"{port_regex}_slot_packet_size"))
            rx_bps = cls.verify_int_not_valueError(
                port_data.get(f"{port_regex}_slot_rx_bits_per_second"))
            rx_errors = cls.verify_int_not_valueError(
                port_data.get(f"{port_regex}_slot_rx_errors"))
            rx_packets = cls.verify_int_not_valueError(
                port_data.get(f"{port_regex}_slot_rx_packets"))
            tx_bps = cls.verify_int_not_valueError(
                port_data.get(f"{port_regex}_slot_tx_bits_per_second"))
            tx_errors = cls.verify_int_not_valueError(
                port_data.get(f"{port_regex}_slot_tx_errors"))
            tx_packets = cls.verify_int_not_valueError(
                port_data.get(f"{port_regex}_slot_tx_packets"))
            speed = cls.verify_int_not_valueError(
                port_data.get(f"{port_regex}_slot_speed"))
            slot = cls.verify_int_not_valueError(
                port_data.get(f"{port_regex}_slot_slot"))
            port_ent = Port(
                port=port,
                bdf=str(port_data.get(f"{port_regex}_slot_bus_dev_func")),
                connection=str(port_data.get(f"{port_regex}_slot_connection")),
                crc=crc,
                device_id=str(port_data.get(f"{port_regex}_slot_device_id")),
                etrack_id=str(port_data.get(f"{port_regex}_slot_etrack_id")),
                link=bool(port_data.get(f"{port_regex}_slot_link")),
                mac_addr=str(port_data.get(f"{port_regex}_slot_mac_address")),
                device_name=str(port_data.get(f"{port_regex}_slot_name")),
                packet_size=pkt_size,
                pattern=str(port_data.get(f"{port_regex}_slot_pattern")),
                remote_mac_addr=str(port_data.get(
                    f"{port_regex}_slot_remote_mac_address")),
                rev_id=str(port_data.get(f"{port_regex}_slot_revision_id")),
                rx_bps=rx_bps,
                rx_errors=rx_errors,
                rx_packets=rx_packets,
                tx_bps=tx_bps,
                tx_errors=tx_errors,
                tx_packets=tx_packets,
                slot=slot,
                speed=speed,
                state=str(port_data.get(f"{port_regex}_slot_state")),
                subsystem_id=str(
                    port_data.get(f"{port_regex}_slot_subsystem_id")),
                subsystem_vendor_id=str(port_data.get(
                    f"{port_regex}_slot_subsystem_vendor_id")),
                vendor_id=str(port_data.get(
                    f"{port_regex}_slot_vendor_id")),
                target_speed=str(port_data.get(
                    f"{port_regex}_target_speed"))
            )
            result["ports"].append(port_ent.to_dict())
        return result

    def to_result(self) -> OrderedDict:
        result_dict = OrderedDict()
        for port in self.ports:
            # if ch.channel_on:
            #    result_dict.update(ch.to_result())
            result_dict.update(port.to_result(suffix=self.device_fmt))

        return result_dict


@dataclass
class DUTTrafficFileEntity(TrafficFileEntity):
    device: str = "dut"
    device_fmt = "DUT"


@dataclass
class LPTrafficFileEntity(TrafficFileEntity):
    device: str = "link_partner"
    device_fmt = "LP"


''' POWER '''


@dataclass
class _PowerCSVBase():
    folder_path: str
    dataframe: pd.DataFrame


@dataclass
class PowerCSVFileEntity(_FileEntityBase, _PowerCSVBase, Entity):
    depth: str = ""

    @classmethod
    def _extract_power_csv_list(cls, df_row: pd.Series) -> t.List[Path]:
        '''
        @param df_row:
        @return:
        '''
        tmpKeys = df_row.to_dict()
        csvList = []

        for key, val in tmpKeys.items():
            if '{}_power'.format(cls.depth) in str(key) and '.csv' in str(
                    key):  # and '.csv' in str(val):
                csvList.append(Path(str(val)))

        return csvList

    @classmethod
    def _extract_power_json(cls, df_row: pd.Series) -> Path:
        '''
        @param df_row:
        @return:
        '''

        tmpKeys = df_row.to_dict()
        print((tmpKeys))
        retJson = Path()

        for key, val in tmpKeys.items():
            if 'capture_power' in str(key) and '.json' in str(key):
                retJson = Path(val)
                break

        return retJson

    @classmethod
    def _power_header_meta_type(cls, header_json_path: Path) -> t.Tuple[t.List,
                                                                        t.List, t.List]:
        '''
        Opens and reads the header json file.

        @param header_path: Path object to header file
        @return: list of headers (with empty headers removed), list of meta,
        and list of type information
        '''
        tmpJson = pd.read_json(header_json_path, typ="dict")

        targetList = ['Time', 'Temperature Setpoint', 'Temperature',
                      '12V_MAIN Volts Setpoint', '12V_MAIN Volts',
                      '12V_MAIN Current', '12V_MAIN Power',
                      '12V_MAIN Slew', '12V_MAIN State',
                      '3.3_AUX Volts Setpoint', '3.3V_AUX Volts Setpoint',
                      '3.3_AUX Volts', '3.3V_AUX Volts',
                      '3.3_AUX Current', '3.3V_AUX Current', '3.3_AUX Power',
                      '3.3V_AUX Power', '3.3_AUX Slew',
                      '3.3V_AUX Slew', '3.3_AUX State', '3.3V_AUX State',
                      'Total Power']
        headList = []
        metaList = []
        typeList = []
        for curDict in tmpJson:

            for item in targetList:
                if curDict['Header'] == item:
                    headList.append(curDict["Header"])
                    metaList.append(curDict["Meta"])
                    typeList.append(curDict["Type"])
                    break
        return headList, metaList, typeList

    @classmethod
    def _find_keys_from_row(cls, df_row: pd.Series) \
            -> t.Tuple[t.List[Path], Path]:
        '''
        This function takes in a row from the input data csv and returns a
        list of power.csv files and the power.json header file.
        @param df_row: dataframe row from data csv
        @return:
            power.csv list -- a list of power.csv path objects
            power.json -- a path object for the power.json file
        '''
        # tmpKeys = df_row.keys().tolist()
        '''
        tmpKeys = df_row.to_dict()
        #print(tmpKeys.items())
        #print(len(tmpKeys))
        #csvList = CapturePowerCSVFileEntity._extract_power_csv_list(df_row)
        #jsonPath = CapturePowerCSVFileEntity._extract_power_json(df_row)
        csvDict = {}
        jsonDict = {}

        # print("working?|")
        for key, val in tmpKeys.items():
            if '_capture_power' in str(key) or '.json' in str(key):  # and '.csv' in str(key):
                print(key, val)
                if '.json' in str(key):
                    jsonDict[key] = val
                if '.csv' in str(key):
                    csvDict[key] = val

        return csvDict, jsonDict
        '''

        csv_path_list = cls._extract_power_csv_list(df_row=df_row)
        json_header_path = cls._extract_power_json(df_row)

        return csv_path_list, json_header_path

    @classmethod
    def _create_power_df(cls, csv_list: t.List[Path], json_header_file: Path) \
            -> pd.DataFrame:
        '''
        Takes in a list of CSV file paths and combines them with the json
        header file to create a dataframe

        @param csv_list:  List of csv Path objects
        @param json_header_file:  Path to json header
        @return: pandas dataframe that combines all the csv files into one
        with the correct headers.
        '''

        jsonExtract = cls._power_header_meta_type(json_header_file)[0]
        print(jsonExtract, type(jsonExtract))
        retDF = pd.DataFrame()
        for curPath in csv_list:
            curDF = pd.read_csv(curPath, header=None)

            retDF = pd.concat([retDF, curDF], ignore_index=False, sort=True)
            print(retDF.head(), retDF.shape)
        retDF.columns = jsonExtract

        return retDF

    @classmethod
    def from_dataframe_row(cls, df_row) -> _FileEntityBase:
        csv_path_list, json_header_path = cls._find_keys_from_row(df_row=df_row)

        power_df = cls._create_power_df(csv_list=csv_path_list,
                                        json_header_file=json_header_path)

        entity_dict = {"folder_path": str(json_header_path.parent.resolve()),
                       "dataframe": power_df}

        e = cls.from_dict(adict=entity_dict)
        return e


'''
Ideas:
- Create more distinct color coding: IE a specific cell color for a particular runID/DUT ect...
- Create micro hierarchies?
- change conditional formatting for red/green
- look into pivot tables
'''


@dataclass
class RunidPowerCSVFileEntity(PowerCSVFileEntity):
    depth: str = "runid"


@dataclass
class CapturePowerCSVFileEntity(PowerCSVFileEntity):
    depth: str = "capture"
