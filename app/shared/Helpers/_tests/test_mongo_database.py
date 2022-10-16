from unittest import TestCase, mock
import logging
import sys

import mongomock

from ..mongo_database import *


class MongoTestCase(TestCase):
    logger = logging.getLogger('MongoTestLogger')
    logger.setLevel(level=logging.DEBUG)

    def setUp(self) -> None:
        self.hdlr = logging.StreamHandler(sys.stderr)
        self.logger.addHandler(hdlr=self.hdlr)

    def tearDown(self) -> None:
        self.logger.removeHandler(self.hdlr)


class MongoProjectTestCase(MongoTestCase):

    # @mock.patch("..mongo_database.MongoProject.db")
    def test_find_one(self):
        insert = ProjectEntity(_id="bob", name="bob")
        MongoProject.insert_one(entity=insert)

        mp = MongoProject.find_one(dut_name="bob")
        self.logger.debug(f"RETURNED: {mp}")
        self.assertDictEqual(insert.to_dict(), mp)

    def test_find_one_empty(self):
        mp = MongoProject.find_one(dut_name="Notbob")
        self.logger.debug(f"RETURNED: {mp}")
        self.assertEqual(None, mp)


class MongoPBATestCase(MongoTestCase):

    # @mock.patch("..mongo_database.MongoProject.db")
    def test_find_one(self):
        insert = PBAEntity.from_dict(adict={"part_number": "J12345-001",
                                            "project": "bob"})
        MongoPBA.insert_one(entity=insert)

        mp = MongoPBA.find_one(part_number="J12345-001")
        self.logger.debug(f"RETURNED: {mp}")
        self.assertDictEqual(insert.to_dict(), mp)

    def test_find_one_empty(self):
        mp = MongoPBA.find_one(part_number="J12345-002")
        self.logger.debug(f"RETURNED: {mp}")
        self.assertEqual(None, mp)


class MongoReworkTestCase(MongoTestCase):

    def test_find_one(self):
        insert = ReworkEntity.from_dict(adict={"rework": 1,
                                               "pba": "12345"})
        MongoRework.insert_one(entity=insert)

        mp = MongoRework.find_one(rework_number=1, pba="12345")
        self.logger.debug(f"RETURNED: {mp}")
        self.assertDictEqual(insert.to_dict(), mp)

    def test_find_one_empty(self):
        mp = MongoRework.find_one(rework_number=1, pba="54321")
        self.logger.debug(f"RETURNED: {mp}")
        self.assertEqual(None, mp)


class MongoSubmissionTestCase(MongoTestCase):

    def test_find_one(self):
        insert = SubmissionEntity(descriptor="DEADBEEF", rework_id="rework_id",
                                  pba="J12345-001", _id="DEADBEEF")
        MongoSubmission.insert_one(entity=insert)

        mp = MongoSubmission.find_one(descriptor="DEADBEEF",
                                      rework_id="rework_id",
                                      pba="J12345-001")
        self.logger.debug(f"RETURNED: {mp}")
        self.assertDictEqual(insert.to_dict(), mp)

    def test_find_one_empty(self):
        mp = MongoSubmission.find_one(descriptor="FAKE", rework_id="FAKE",
                                      pba="FAKE")
        self.logger.debug(f"RETURNED: {mp}")
        self.assertEqual(None, mp)


class MongoRunidTestCase(MongoTestCase):

    def test_find_one(self):
        insert = RunidEntity(runid=10, _id=10)
        MongoRunid.insert_one(entity=insert)

        mp = MongoRunid.find_one(run_id=10)
        self.logger.debug(f"RETURNED: {mp}")
        self.assertDictEqual(insert.to_dict(), mp)

    def test_find_one_empty(self):
        mp = MongoRunid.find_one(run_id=11)
        self.logger.debug(f"RETURNED: {mp}")
        self.assertEqual(None, mp)
        
    def test_insert_or_update_one(self):
        import time
        r = RunidEntity(runid=1, _id=1)
        MongoRunid.insert_or_update_one(entity=r)
        print(MongoRunid.find_one(run_id=1))
        time.sleep(10)
        MongoRunid.insert_or_update_one(entity=r)
        print(MongoRunid.find_one(run_id=1))


class MongoAutomationTestTestCase(MongoTestCase):

    def test_find_one(self):
        insert = AutomationTestEntity(_id="TestTest", name="TestTest")
        MongoAutomationTest.insert_one(entity=insert)

        mp = MongoAutomationTest.find_one(name="TestTest")
        self.logger.debug(f"RETURNED: {mp}")
        self.assertDictEqual(insert.to_dict(), mp)

    def test_find_one_empty(self):
        mp = MongoAutomationTest.find_one(name="FakeTest")
        self.logger.debug(f"RETURNED: {mp}")
        self.assertEqual(None, mp)


class MongoDataCaptureTestCase(MongoTestCase):

    def test_find_one(self):
        insert = WaveformCaptureEntity(_id=1, number=1, runid=1)
        MongoDataCapture.insert_one(entity=insert)

        mp = MongoDataCapture.find_one(capture_number=1, runid=1)
        self.logger.debug(f"RETURNED: {mp}")
        self.assertDictEqual(insert.to_dict(), mp)

    def test_find_one_empty(self):
        mp = MongoDataCapture.find_one(capture_number=10, runid=10)
        self.logger.debug(f"RETURNED: {mp}")
        self.assertEqual(None, mp)


class MongoWaveformTestCase(MongoTestCase):

    def test_find_one(self):
        insert = WaveformEntity(_id="bob", testpoint="bob", runid=10,
                                capture=10, units="A", location="",
                                scope_channel=1, steady_state_pk2pk=11.1,
                                max=10.0, min=10.1, steady_state_max=12.1,
                                steady_state_mean=1.1, steady_state_min=20.2,
                                user_reviewed=False, downsample=[])
        MongoWaveform.insert_one(entity=insert)

        mp = MongoWaveform.find_one(testpoint="bob", run_id=10, capture=10)
        self.logger.debug(f"RETURNED: {mp}")
        self.assertDictEqual(insert.to_dict(), mp)

    def test_find_one_empty(self):
        mp = MongoWaveform.find_one(testpoint="Not Bob", run_id=10, capture=10)
        self.logger.debug(f"RETURNED: {mp}")
        self.assertEqual(None, mp)
