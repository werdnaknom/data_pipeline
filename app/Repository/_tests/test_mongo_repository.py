from unittest import TestCase, mock
import typing as t
import os
import random
import logging
import sys
import string

import pymongo
import mongomock
from faker import Faker
import numpy as np

from basicTestCase.basic_test_case import BasicTestCase
from app.shared.Entities.entities import *

from app.Repository.repository import MongoRepository


def create_fake_product_entities(num: int) -> t.List[ProjectEntity]:
    faker = Faker()
    entity_list = []
    for _ in range(num):
        proj_name = faker.name()
        silicon_list = faker.words()
        entity = ProjectEntity(name=proj_name, silicon=silicon_list)
        entity_list.append(entity)
    return entity_list


def create_fake_pba_entities(num: int) -> t.List[PBAEntity]:
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


def create_fake_rework_entities(num: int) -> t.List[ReworkEntity]:
    faker = Faker()
    entity_list = []
    letters = 'ABCDEFGHIJKLM'
    for _ in range(num):
        part_number = random.choice(letters) + ''.join(random.sample(
            '0123456789', 4)) + "-" + ''.join(random.sample('0123456789',
                                                            3))
        rework = faker.random_number()
        notes = faker.sentence()
        eetrack_id = '0x8000' + ''.join(random.sample(string.hexdigits.upper(),
                                                      4))

        entity = ReworkEntity(pba=part_number, rework=rework, notes=notes,
                              eetrack_id=eetrack_id)
        entity_list.append(entity)
    return entity_list


def create_fake_submission_entities(num: int) -> t.List[SubmissionEntity]:
    faker = Faker()
    entity_list = []
    letters = 'ABCDEFGHIJKLM'
    for _ in range(num):
        desc = ''.join(random.sample(string.hexdigits.upper(), 6))
        rework = faker.random_number()
        pba = random.choice(letters) + ''.join(random.sample(
            '0123456789', 4)) + "-" + ''.join(random.sample('0123456789',
                                                            3))
        entity = SubmissionEntity(submission=desc, rework=rework, pba=pba)
        entity_list.append(entity)
    return entity_list


def create_fake_runid_entities(num: int) -> t.List[RunidEntity]:
    faker = Faker()
    entity_list = []
    for _ in range(num):
        runid = faker.random_number()
        system_entity = SystemInfoFileEntity(probes=[],
                                             scope_serial_number=faker.word(),
                                             power_supply_serial_number=faker.word(),
                                             ats_version=faker.word())
        status_entity = StatusFileEntity(status="Complete",
                                         time=faker.time(),
                                         info=faker.sentence(),
                                         runtime_hours=1,
                                         runtime_minutes=10,
                                         runtime_total_seconds=12331,
                                         runtime_seconds=43)
        testrun_entity = TestRunFileEntity(dut=faker.name(),
                                           pba=faker.word(),
                                           rework="1241",
                                           serial_number="bakghea",
                                           technician=faker.name(),
                                           test_station=faker.name(),
                                           configuration="412",
                                           board_id=10,
                                           test_points={})
        comments_entity = CommentsFileEntity(comments={})

        entity = RunidEntity(runid=runid,
                             status=status_entity,
                             system_info=system_entity,
                             testrun=testrun_entity,
                             comments=comments_entity
                             )
        entity_list.append(entity)
    return entity_list


def create_fake_automation_test_entities(num: int) -> t.List[
    AutomationTestEntity]:
    faker = Faker()
    entity_list = []
    for _ in range(num):
        name = random.choice(["EthAgent", "Aux To Main", "Load Profile",
                              "Ripple", "Scripts"])
        notes = faker.sentence()
        entity = AutomationTestEntity(name=name, notes=notes)
        entity_list.append(entity)
    return entity_list


def create_fake_datacapture_entities(num: int) -> t.List[WaveformCaptureEntity]:
    faker = Faker()
    entity_list = []
    for _ in range(num):
        capture = faker.random_number()
        runid = faker.random_number()
        test_category = faker.name()
        settings_entity = CaptureSettingsEntity(
            initial_x=float(faker.random_number()),
            x_increment=float(faker.random_number()),
            compress=faker.boolean())
        environment_entity = CaptureEnvironmentFileEntity(
            chamber_setpoint=faker.random_number(), dut_on=faker.boolean(),
            power_supply_channels=[])
        entity = WaveformCaptureEntity(capture=capture, runid=runid,
                                       test_category=test_category,
                                       capture_settings=settings_entity,
                                       environment=environment_entity
                                       )
        entity_list.append(entity)
    return entity_list


def create_fake_waveform_entities(num: int) -> t.List[WaveformEntity]:
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
                                steady_state_pk2pk=round(random.random(), 3),
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


class MongoRepositoryTestCase(BasicTestCase):
    logger_name = 'MongoRepositoryTestLogger'

    @mongomock.patch(servers=(('server.example.com', 27017),))
    def _setUp(self) -> None:
        self.location = r'\\npo\coos\LNO_Validation\Validation_Data\_data\ATS ' \
                        r'2.0\Mentor Harbor\K31123-003\RW00\BB063A\906\Tests\Aux ' \
                        r'To Main\2\CH1.bin'

        self.repo = MongoRepository('server.example.com')

    def _log_assert_equal(self, itemA, itemB):
        self.logger.debug(msg=f"Item[{itemA}] should equal Item[{itemB}]")
        self.assertEqual(itemA, itemB)

    def _test_insert_one(self, entity):
        self.logger.debug(msg=f"\nInserting[{entity}] into database")

        inserted = self.repo.insert_one(entity=entity)
        self.assertIsInstance(inserted, str)

        self._log_assert_equal(itemA=inserted,
                               itemB=entity._id)

        found = self.repo._find_one(
            collection=self.repo.get_collection(entity.get_collection()),
            filters=entity.get_filter())
        self.assertIsInstance(found, dict)

        self.logger.debug(msg=f"Found[{found}] from database!")

        found_entity = entity.from_dict(adict=found)
        self.logger.debug(msg=f"Created[{found_entity}] from found dict!")

        self.assertEqual(found_entity, entity)

    def test_init(self):
        r = MongoRepository(mongo_uri="mongodb://localhost:27017")

        self.assertEqual(r._mongo_uri, "mongodb://localhost:27017")
        self._log_assert_equal(r._db_name, "PostProcessing")
        self.assertIsInstance(r.db, pymongo.database.Database)

        self._log_assert_equal(r.collection_project.name,
                               ProjectEntity.get_collection())
        self.assertIsInstance(r.collection_project,
                              pymongo.collection.Collection)

        self._log_assert_equal(r.collection_pba.name,
                               PBAEntity.get_collection())
        self.assertIsInstance(r.collection_pba, pymongo.collection.Collection)

        self._log_assert_equal(r.collection_rework.name,
                               ReworkEntity.get_collection())
        self.assertIsInstance(r.collection_rework,
                              pymongo.collection.Collection)

        self._log_assert_equal(r.collection_submission.name,
                               SubmissionEntity.get_collection())
        self.assertIsInstance(r.collection_submission,
                              pymongo.collection.Collection)

        self._log_assert_equal(r.collection_runid.name,
                               RunidEntity.get_collection())
        self.assertIsInstance(r.collection_runid, pymongo.collection.Collection)

        self._log_assert_equal(r.collection_automation_test.name,
                               AutomationTestEntity.get_collection())
        self.assertIsInstance(r.collection_automation_test,
                              pymongo.collection.Collection)

        self._log_assert_equal(r.collection_waveform_capture.name,
                               WaveformCaptureEntity.get_collection())
        self.assertIsInstance(r.collection_waveform_capture,
                              pymongo.collection.Collection)

        self._log_assert_equal(r.collection_waveform.name,
                               WaveformEntity.get_collection())
        self.assertIsInstance(r.collection_waveform,
                              pymongo.collection.Collection)

    def test_insert_find_one_project(self):
        fake_projects = create_fake_product_entities(10)

        for project_entity in fake_projects:
            self._test_insert_one(entity=project_entity)

    def test_insert_find_project_id(self):
        fake_projects = create_fake_product_entities(10)

        for project_entity in fake_projects:
            found = self.repo.find_project_id(project_name=project_entity.name)
            self.assertEqual(found, "")
            self.repo.insert_one(entity=project_entity)
            found = self.repo.find_project_id(project_name=project_entity.name)
            self.assertEqual(found, project_entity._id)

    def test_insert_find_one_pba(self):
        for entity in create_fake_pba_entities(10):
            self._test_insert_one(entity=entity)

    def test_insert_find_one_rework(self):

        for entity in create_fake_rework_entities(10):
            self._test_insert_one(entity=entity)

    def test_insert_find_one_submission(self):

        for entity in create_fake_submission_entities(10):
            self._test_insert_one(entity=entity)

    def test_insert_find_one_runid(self):
        for entity in create_fake_runid_entities(10):
            self._test_insert_one(entity=entity)

    def test_insert_find_one_test(self):

        for entity in create_fake_automation_test_entities(10):
            self._test_insert_one(entity=entity)

    def test_insert_find_one_datacapture(self):

        for entity in create_fake_datacapture_entities(10):
            self._test_insert_one(entity=entity)

    def test_insert_find_one_waveform(self):

        for entity in create_fake_waveform_entities(10):
            self._test_insert_one(entity=entity)

    def test_find_waveform_id(self):
        wfs = create_fake_waveform_entities(10)

        for wf in wfs:
            wf.downsample = None

        for x in range(100):
            for wf in wfs:

                self.logger.debug(f"{wf.testpoint}")
                exists = self.repo.find_waveform_id(testpoint=wf.testpoint,
                                                    capture=wf.capture,
                                                    runid=wf.runid,
                                                    test_category=wf.test_category,
                                                    scope_channel=wf.scope_channel)
                if exists:
                    print("EXISTS!", exists)
                    self.assertNotEqual(x, 0)
                else:
                    inserted = self.repo.insert_waveform(wf)
                    print("INSERTED: ", inserted)
                    self.assertEqual(x, 0)

    def test_find_waveform_id_real_dataframe(self):
        df = self._helper_load_capture_df()

        for x in range(100):
            for i, row in df.iterrows():
                wf = WaveformEntity(test_category=row["test_category"],
                                    units="V", location=row['location'],
                                    scope_channel=row['scope_channel'],
                                    capture=row['capture'], runid=row['runid'],
                                    testpoint=row['testpoint'])

                self.logger.debug(f"{wf.testpoint}")
                exists = self.repo.find_waveform_id(testpoint=wf.testpoint,
                                                    capture=wf.capture,
                                                    runid=wf.runid,
                                                    test_category=wf.test_category,
                                                    scope_channel=wf.scope_channel)
                if exists:
                    print("EXISTS!", exists)
                    self.assertNotEqual(x, 0)
                else:
                    inserted = self.repo.insert_waveform(wf)
                    print("INSERTED: ", inserted)
                    self.assertEqual(x, 0)

    def test_find_project_id_real_dataframe(self):
        df = self._helper_load_capture_df()

        for x in range(10):
            by = ['dut']
            for filt, df in df.groupby(by):
                print(filt)
                find = self.repo.find_project_id(filt)
                if x == 0:
                    self.logger.debug(f"At X=0, find is : {find}")
                    self.assertEqual(find, "")
                    self.repo.insert_one(entity=ProjectEntity(name=filt))
                else:
                    self.logger.debug(f"At X>0, find is : {find}")
                    self.assertEqual(find, filt.replace(" ", "").lower())

    def test_find_pba_id_real_dataframe(self):
        df = self._helper_load_capture_df()

        for x in range(10):
            by = ['dut', 'pba']
            for filt, df in df.groupby(by):
                find = self.repo.find_pba_id(part_number=filt[1],
                                             project=filt[0])
                if x == 0:
                    print("PBA COUNT: ",
                          self.repo.collection_pba.count_documents({}))
                    self.logger.debug(f"At X=0, find is : {find}")
                    self.assertEqual(find, "")
                    self.repo.insert_one(entity=PBAEntity(part_number=filt[1],
                                                          project=filt[0]))
                else:
                    self.logger.debug(f"At X>0, find is : {find}")
                    self.assertEqual(find, find.replace(" ", ""))

    def test_find_rework_id_real_dataframe(self):
        df = self._helper_load_capture_df()

        for x in range(10):
            by = ['pba', 'rework']
            for filt, df in df.groupby(by):
                find = self.repo.find_rework_id(pba=filt[0],
                                                rework_number=filt[1])
                # print([x for x in self.repo.collection_rework.find({})])
                if x == 0:
                    find_count = self.repo.collection_rework.count_documents({})
                    self.logger.debug(f"Found count is {find_count}")
                    self.assertEqual(find_count, 0)
                    self.logger.debug(f"At X=0, find is : {find}")
                    self.assertEqual(find, "")
                    self.repo.insert_one(entity=ReworkEntity(pba=filt[0],
                                                             rework=filt[1]))
                    find_count = self.repo.collection_rework.count_documents({})
                else:
                    x_count = self.repo.collection_rework.count_documents({})
                    self.assertEqual(find_count, x_count)
                    self.logger.debug(f"At x>0, Found count is"
                                      f" {find_count}")
                    # self.assertEqual(find_count, 1)
                    self.logger.debug(f"At X>0, find is : {find}")
                    self.assertEqual(find, f"{filt[0]}_REWORK_{filt[1]}")

    def test_find_submission_id_real_dataframe(self):
        df = self._helper_load_capture_df()

        for x in range(10):
            by = ['pba', 'rework', "serial_number"]
            for filt, df in df.groupby(by):
                find = self.repo.find_submission_id(submission=filt[2],
                                                    pba=filt[0],
                                                    rework=filt[1])
                # print([x for x in self.repo.collection_rework.find({})])
                if x == 0:
                    find_count = self.repo.collection_submission.count_documents(
                        {})
                    self.logger.debug(f"Found count is {find_count}")
                    self.assertEqual(find_count, 0)
                    self.logger.debug(f"At X=0, find is : {find}")
                    self.assertEqual(find, "")
                    self.repo.insert_one(entity=SubmissionEntity(
                        submission=filt[2], rework=filt[1], pba=filt[0]))
                    find_count = self.repo.collection_submission.count_documents(
                        {})
                else:
                    x_count = self.repo.collection_submission.count_documents(
                        {})
                    self.assertEqual(find_count, x_count)
                    self.logger.debug(f"At x>0, Found count is"
                                      f" {find_count}")
                    # self.assertEqual(find_count, 1)
                    self.logger.debug(f"At X>0, find is : {find}")
                    self.assertEqual(find, f"{filt[2]}_{filt[0]}_{filt[1]}")

    def test_find_runid_id_real_dataframe(self):
        df = self._helper_load_capture_df()

        for x in range(10):
            by = ['runid']
            for filt, df in df.groupby(by):
                find = self.repo.find_run_id(runid=filt)
                if x == 0:
                    find_count = self.repo.collection_runid.count_documents({})
                    self.logger.debug(f"Found count is {find_count}")
                    self.assertEqual(find_count, 0)
                    self.logger.debug(f"At X=0, find is : {find}")
                    self.assertEqual(find, "")
                    entity = RunidEntity.from_dataframe_row(df_row=df.iloc[0])
                    self.repo.insert_one(entity=entity)
                    find_count = self.repo.collection_runid.count_documents({})
                else:
                    x_count = self.repo.collection_runid.count_documents({})
                    self.assertEqual(find_count, x_count)
                    self.logger.debug(f"At x>0, Found count is"
                                      f" {find_count}")
                    # self.assertEqual(find_count, 1)
                    self.logger.debug(f"At X>0, find is : {find}")
                    self.assertEqual(find, f"{filt}")

    def test_find_automation_test_real_dataframe(self):
        df = self._helper_load_capture_df()

        for x in range(10):
            by = ['test_category']
            for filt, df in df.groupby(by):
                find = self.repo.find_automation_test_id(test_name=filt)
                if x == 0:
                    find_count = self.repo.collection_automation_test.count_documents(
                        {})
                    self.logger.debug(f"Found count is {find_count}")
                    self.assertEqual(find_count, 0)
                    self.logger.debug(f"At X=0, find is : {find}")
                    self.assertEqual(find, "")
                    self.repo.insert_one(entity=AutomationTestEntity(name=filt))
                    find_count = self.repo.collection_automation_test.count_documents(
                        {})
                else:
                    x_count = self.repo.collection_automation_test.count_documents(
                        {})
                    self.assertEqual(find_count, x_count)
                    self.logger.debug(f"At x>0, Found count is"
                                      f" {find_count}")
                    # self.assertEqual(find_count, 1)
                    self.logger.debug(f"At X>0, find is : {find}")
                    self.assertEqual(find, filt.replace(" ", "").lower())

    def test_find_datacapture_real_dataframe(self):
        df = self._helper_load_capture_df()

        for x in range(10):
            by = ['test_category', "runid", "capture"]
            for filt, df in df.groupby(by):
                find = self.repo.find_waveform_capture_id(capture=filt[2],
                                                          runid=filt[
                                                              1], test=filt[0])
                if x == 0:
                    find_count = self.repo.collection_waveform_capture.count_documents(
                        {})
                    self.logger.debug(f"Found count is {find_count}")
                    self.assertEqual(find_count, 0)
                    self.logger.debug(f"At X=0, find is : {find}")
                    self.assertEqual(find, "")
                    self.repo.insert_one(
                        entity=WaveformCaptureEntity.from_dataframe_row(
                            df_row=df.iloc[0]))
                    find_count = self.repo.collection_waveform_capture.count_documents(
                        {})
                else:
                    x_count = self.repo.collection_waveform_capture.count_documents(
                        {})
                    self.assertEqual(find_count, x_count)
                    self.logger.debug(f"At x>0, Found count is"
                                      f" {find_count}")
                    # self.assertEqual(find_count, 1)
                    self.logger.debug(f"At X>0, find is : {find}")
                    self.assertEqual(find, f"waveform_{filt[1]}_"
                                           f"{filt[0].replace(' ', '').lower()}"
                                           f"_{filt[2]}")
