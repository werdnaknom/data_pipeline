import typing as t
from unittest import TestCase
import logging
import sys
import pickle
from pathlib import Path
import random
import string

from faker import Faker

from app.shared.Entities.entities import *
from app.shared.Entities.file_entities import Port

import pandas as pd


class BasicTestCase(TestCase):
    logger_name = "BasicTestCase"
    logger = logging.getLogger('WaveformEntityTestLogger')
    logger.setLevel(level=logging.DEBUG)
    TEST_FILE_FOLDER = r"C:\Users\ammonk\OneDrive - Intel Corporation\Desktop\Test_Folder\fake_uploads"

    def setUp(self) -> None:
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(level=logging.DEBUG)
        self.hdlr = logging.StreamHandler(sys.stderr)
        self.logger.addHandler(hdlr=self.hdlr)
        self._setUp()

    def _setUp(self):
        '''
        Should be overridden by child classes if they have any specific setup
        requirements
        '''
        pass

    def tearDown(self) -> None:
        self.logger.removeHandler(self.hdlr)

    def _helper_load_waveform_group(self, groupnum: int):
        assert groupnum >= 0
        assert groupnum < 94, "groupnum must be between 0 and 93, " \
                              f"not {groupnum}"
        p = Path(self.TEST_FILE_FOLDER).joinpath("capture_groups")
        filename = f"group{groupnum}_wfs.pkl"
        filepath = p.joinpath(filename)
        assert filepath.exists(), f"HELPER load_waveform_group FAILED BECAUSE" \
                                  f" {filepath} DOESN'T EXIST!"

        wfs = self._helper_read_pickle(pickle_path=filepath)
        self.logger.debug(msg=f"Waveforms loaded: {wfs}")
        return wfs

    def _helper_get_file(self, filename):
        p = Path(self.TEST_FILE_FOLDER)
        filepath = p.joinpath(filename)
        assert filepath.exists(), f"HELPER FILE FAILED BECAUSE {filepath} " \
                                  "DOESN'T EXIST!"
        return filepath

    def _helper_read_pickle(self, pickle_path):
        with open(pickle_path, 'rb') as f:
            result = pickle.load(f)
        return result

    def _helper_load_waveforms(self) -> t.List[WaveformEntity]:
        wfs = self._helper_load_waveform_group(groupnum=0)
        '''
        pickled_waveforms_path = self._helper_get_file(
            filename="lp_capture_waveforms.pkl")
        wfs = self._helper_read_pickle(pickled_waveforms_path)
        self.logger.debug(msg=f"Waveforms loaded: {wfs}")
        '''
        return wfs

    def _helper_load_post_processed_df(self) -> pd.DataFrame:
        picked_df_path = self._helper_get_file(
            filename="post_processed_saved_df.pkl")
        df = self._helper_read_pickle(picked_df_path)
        self.logger.debug(msg=f"Dataframe of shape: {df.shape} loaded")
        return df

    def _helper_load_capture_df(self):
        pickled_df_path = self._helper_get_file(
            filename="lp_capture_group_df.pkl")
        df = self._helper_read_pickle(pickled_df_path)
        self.logger.debug(msg=f"Dataframe of shape: {df.shape} loaded")
        return df

    def _helper_load_input_load_profile_df(self):
        pickled_df_path = self._helper_get_file(filename="load_profile_df.pkl")
        df = self._helper_read_pickle(pickled_df_path)
        self.logger.debug(f"Load Profile input dataframe of shape {df.shape} "
                          f"loaded")
        return df

    def _helper_load_aux_to_main_csv(self) -> pd.DataFrame:
        test_file = self._helper_get_file(
            filename="MentorHarbor_aux_to_main.csv")
        return pd.read_csv(test_file)

    def _helper_load_load_profile_csv(self) -> pd.DataFrame:
        test_file = self._helper_get_file(
            filename="mentor_harbor_load_profile.csv")
        return pd.read_csv(test_file)

    def _helper_xlsx_path(self):
        path = self._helper_get_file(filename="load_profile_userInput.xlsx")
        return path

    def _helper_load_user_xlsx(self):
        test_file = self._helper_xlsx_path()
        return pd.read_excel(test_file, sheet_name=None)

    def create_fake_product_entities(self, num: int) -> t.List[ProjectEntity]:
        faker = Faker()
        entity_list = []
        for _ in range(num):
            proj_name = faker.name()
            silicon_list = faker.words()
            entity = ProjectEntity(name=proj_name, silicon=silicon_list)
            entity_list.append(entity)
        return entity_list

    def create_fake_pba_entities(self, num: int) -> t.List[PBAEntity]:
        faker = Faker()
        entity_list = []

        letters = 'ABCDEFGHIJKLM'

        for _ in range(num):
            part_number = random.choice(letters) + ''.join(random.sample(
                '0123456789', 4)) + "-" + ''.join(random.sample('0123456789',
                                                                3))
            proj_name = faker.name()
            random_string = faker.sentence()
            reworks = [''.join([random.choice(letters) for _ in range(
                random.randrange(10))]) for _ in range(random.randrange(10))]
            customers = [faker.name() for _ in range(random.randrange(10))]
            entity = PBAEntity(part_number=part_number, project=proj_name,
                               notes=random_string, reworks=reworks,
                               customers=customers)
            entity_list.append(entity)
        return entity_list

    def create_fake_rework_entities(self, num: int) -> t.List[ReworkEntity]:
        faker = Faker()
        entity_list = []
        letters = 'ABCDEFGHIJKLM'
        for _ in range(num):
            part_number = random.choice(letters) + ''.join(random.sample(
                '0123456789', 4)) + "-" + ''.join(random.sample('0123456789',
                                                                3))
            rework = faker.random_number()
            notes = faker.sentence()
            eetrack_id = '0x8000' + ''.join(
                random.sample(string.hexdigits.upper(),
                              4))

            entity = ReworkEntity(pba=part_number, rework=rework, notes=notes,
                                  eetrack_id=eetrack_id)
            entity_list.append(entity)
        return entity_list

    def create_fake_submission_entities(self, num: int) -> t.List[
        SubmissionEntity]:
        faker = Faker()
        entity_list = []
        letters = 'ABCDEFGHIJKLM'
        for _ in range(num):
            desc = ''.join(random.sample(string.hexdigits.upper(), 6))
            rework = faker.random_number()
            pba = random.choice(letters) + ''.join(random.sample(
                '0123456789', 4)) + "-" + ''.join(random.sample('0123456789',
                                                                3))
            entity = SubmissionEntity(descriptor=desc, rework=rework, pba=pba)
            entity_list.append(entity)
        return entity_list

    def create_fake_runid_entities(self, num: int) -> t.List[RunidEntity]:
        faker = Faker()
        entity_list = []
        for _ in range(num):
            runid = faker.random_number()
            entity = RunidEntity(runid=runid, comments=CommentsFileEntity(
                comments={}),
                                 status=StatusFileEntity(status="Pass",
                                                         time=faker.date_time(),
                                                         info="",
                                                         runtime_total_seconds=faker.random_number(),
                                                         runtime_hours=3,
                                                         runtime_seconds=45,
                                                         runtime_minutes=2),
                                 system_info=SystemInfoFileEntity(probes=[]),
                                 testrun=TestRunFileEntity(dut="", pba="",
                                                           rework="",
                                                           serial_number="",
                                                           technician="",
                                                           test_points={},
                                                           test_station="",
                                                           configuration="",
                                                           board_id=faker.random_number()))
            entity_list.append(entity)
        return entity_list

    def create_fake_automation_test_entities(self, num: int) -> t.List[
        AutomationTestEntity]:
        faker = Faker()
        entity_list = []
        for _ in range(num):
            name = faker.name()
            notes = faker.sentence()
            entity = AutomationTestEntity(name=name, notes=notes)
            entity_list.append(entity)
        return entity_list

    def create_fake_datacapture_entities(self, num: int) -> t.List[
        WaveformCaptureEntity]:
        faker = Faker()
        entity_list = []
        for _ in range(num):
            capture = faker.random_number()
            runid = faker.random_number()
            test_category = faker.name()
            entity = WaveformCaptureEntity(capture=capture, runid=runid,
                                           test_category=test_category,
                                           environment=self.create_fake_environment_entity(),
                                           settings=self.create_fake_settings_entity())
            entity_list.append(entity)
        return entity_list

    def create_fake_environment_entity(self) -> CaptureEnvironmentFileEntity:
        faker = Faker()
        environment = CaptureEnvironmentFileEntity(
            chamber_setpoint=faker.random_number(), dut_on=faker.boolean())
        return environment

    def create_fake_settings_entity(self) -> CaptureSettingsEntity:
        faker = Faker()
        settings = CaptureSettingsEntity(
            initial_x=0,
            x_increment=faker.random_number() ** - faker.random_number(),
            compress=faker.boolean()
        )
        return settings

    def create_fake_traffic(self) -> t.Tuple[
        DUTTrafficFileEntity, LPTrafficFileEntity]:
        faker = Faker()
        dut_ports = []
        lp_ports = []
        rx_bps = faker.random_choices(
            [46275384839, 45693235293, 44721662158, 44889973146, 45353774789,
             46041385891, 45382534847, 44807145961, 44852326545], 1)[0]
        tx_bps = faker.random_choices(
            [46275384839, 45693235293, 44721662158, 44889973146, 45353774789,
             46041385891, 45382534847, 44807145961, 44852326545], 1)[0]
        rx_packets = faker.random_choices(
            [419352678, 416737779, 412615892, 414722962, 419335397, 414577793,
             428435986, 415585908, 413272740], 1)[0]
        tx_packets = faker.random_choices(
            [419352678, 416737779, 412615892, 414722962, 419335397, 414577793,
             428435986, 415585908, 413272740], 1)[0]

        for port_num in range(0, faker.random_digit() + 1):
            for l in [dut_ports, lp_ports]:
                port_ent = Port(
                    port=port_num,
                    bdf=faker.word(),
                    connection=faker.ipv4(),
                    crc=faker.random_digit(),
                    device_id="device_id",
                    etrack_id="etrack_id",
                    link=faker.boolean(),
                    mac_addr=faker.mac_address(),
                    device_name="Intel Device Name",
                    packet_size=faker.random_choices([1024, 1500, 64, 128, 256],
                                                     1)[0],
                    pattern="random pattern",
                    remote_mac_addr=faker.mac_address(),
                    rev_id=faker.random_digit(),
                    rx_bps=rx_bps,
                    rx_errors=0,
                    rx_packets=rx_packets,
                    tx_bps=tx_bps,
                    tx_errors=0,
                    tx_packets=tx_packets,
                    slot=faker.word(),
                    speed=50000,
                    state="random state",
                    subsystem_id="random_subsystem",
                    subsystem_vendor_id="random_sub vendor_id",
                    vendor_id="vendor_id",
                    target_speed="AUTO"
                )
                l.append(port_ent)

        dut = DUTTrafficFileEntity(ports=dut_ports)
        lp = LPTrafficFileEntity(ports=lp_ports)
        return dut, lp

    def create_fake_traffic_capture_entities(self, num: int) -> t.List[
        EthAgentCaptureEntity]:
        faker = Faker()
        entity_list = []
        for _ in range(num):
            capture = faker.random_number()
            runid = faker.random_number()
            test_category = faker.name()
            dut, lp = self.create_fake_traffic()
            entity = EthAgentCaptureEntity(capture=capture, runid=runid,
                                           test_category=test_category,
                                           environment=self.create_fake_environment_entity(),
                                           dut=dut,
                                           lp=lp)
            entity_list.append(entity)
        return entity_list

    def create_fake_waveform_entities(self, num: int) -> t.List[WaveformEntity]:
        faker = Faker()
        entity_list = []
        for _ in range(num):
            capture = faker.random_number()
            runid = faker.random_number()
            test_category = faker.name()
            testpoint = faker.word()
            units = random.choice("VA")
            location = faker.file_path(depth=6, extension="bin")
            r = np.random.rand(2, 1000)
            downsample = [r[0].tolist(), r[1].tolist()]
            # downsample = []
            entity = WaveformEntity(capture=capture, runid=runid,
                                    test_category=test_category,
                                    testpoint=testpoint,
                                    units=units,
                                    location=location,
                                    scope_channel=random.choice("12345678"),
                                    steady_state_pk2pk=round(random.random(),
                                                             3),
                                    steady_state_max=round(random.random(), 3),
                                    steady_state_mean=round(random.random(), 3),
                                    steady_state_min=round(random.random(), 3),
                                    max=round(random.random(), 3),
                                    min=round(random.random(), 3),
                                    user_reviewed=random.choice([True, False]),
                                    downsample=downsample,
                                    )

            entity_list.append(entity)
        return entity_list
