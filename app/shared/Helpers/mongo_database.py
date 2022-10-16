from app.shared.Entities.entities import *

from app import mongo

import mongomock


class MongoEntity():
    db = mongomock.MongoClient()['TestDatabase']
    collection = None
    base_entity = None

    @classmethod
    def get_collection(cls):
        return cls.db[cls.base_entity._type]

    @classmethod
    def find_one(cls, **kwargs):
        raise NotImplementedError

    @classmethod
    def insert_one(cls, entity: Entity):
        assert isinstance(entity, cls.base_entity)
        entity_dict = entity.to_dict()
        inserted = cls.get_collection().insert_one(entity_dict)
        return inserted

    @classmethod
    def insert_many(cls, entity_list: t.List[Entity]):
        entity_dicts_list = []
        for entity in entity_list:
            assert isinstance(entity, cls.base_entity), \
                "Entity must be of type {entity}".format(
                    entity=cls.base_entity._type)
            entity_dicts_list.append(entity.to_dict())
        bulk_insert = cls.get_collection().insert_many(entity_dicts_list)
        return bulk_insert

    @classmethod
    def insert_or_update_one(cls, entity: Entity, upsert: bool = True):
        cls._verify_entity(entity=entity)
        update_dict= {"$set": {"modified_date": datetime.datetime.utcnow()}}
        

        update = cls.get_collection().update_one(filter=entity.get_filter(),
                                                 update=update_dict,
                                                 upsert=upsert)
        return update

    @classmethod
    def _verify_entity(cls, entity: Entity):
        assert isinstance(entity, cls.base_entity), \
            "Entity must be of type {etype} but was {wrong}".format(
                etype=cls.base_entity._type, wrong=entity._type)

    @classmethod
    def _verify_entity_list(cls, entity_list: t.List[Entity]):
        for entity in entity_list:
            cls._verify_entity(entity)


class MongoProject(MongoEntity):
    base_entity = ProjectEntity

    @classmethod
    def find_one(cls, dut_name: str):
        return cls.get_collection().find_one({"name": dut_name})


class MongoPBA(MongoEntity):
    base_entity = PBAEntity

    @classmethod
    def find_one(cls, part_number: str):
        return cls.get_collection().find_one({"part_number": part_number})


class MongoRework(MongoEntity):
    base_entity = ReworkEntity

    @classmethod
    def find_one(cls, rework_number: int, pba: str):
        return cls.get_collection().find_one({"rework": rework_number,
                                              "pba": pba})


class MongoSubmission(MongoEntity):
    base_entity = SubmissionEntity

    @classmethod
    def find_one(cls, descriptor: str, rework_id: str, pba: str):
        return cls.get_collection().find_one({"submission": descriptor,
                                              "rework_id": rework_id,
                                              "pba": pba})


class MongoRunid(MongoEntity):
    base_entity = RunidEntity

    @classmethod
    def find_one(cls, run_id: int):
        return cls.get_collection().find_one({"runid": run_id})


class MongoAutomationTest(MongoEntity):
    base_entity = AutomationTestEntity

    @classmethod
    def find_one(cls, name: str):
        return cls.get_collection().find_one({"name": name})


class MongoDataCapture(MongoEntity):
    base_entity = WaveformCaptureEntity

    @classmethod
    def find_one(cls, capture_number: int, runid: int):
        return cls.get_collection().find_one({"capture": capture_number,
                                              "runid": runid})


class MongoWaveform(MongoEntity):
    base_entity = WaveformEntity

    @classmethod
    def find_one(cls, testpoint: str, run_id: int, capture: int):
        return cls.get_collection().find_one({"testpoint": testpoint,
                                              "runid": run_id,
                                              "capture": capture})
