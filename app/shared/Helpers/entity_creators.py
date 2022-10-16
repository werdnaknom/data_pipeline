import typing as t
from bson import ObjectId
import datetime

import numpy as np
from pathlib import Path

from app.shared.Entities.entities import Entity, ProjectEntity, PBAEntity, \
    ReworkEntity, RunidEntity, SiliconEntity, \
    WaveformCaptureEntity, SubmissionEntity, AutomationTestEntity, WaveformEntity
from app.shared.Entities.entities import PROJECT_DESCRIPTOR, LIST_OF_SILICON

from app import mongo

ENTITY_TYPE = t.TypeVar("ENTITY_TYPE", Entity, ProjectEntity, PBAEntity,
                        ReworkEntity, RunidEntity,
                        WaveformCaptureEntity, SubmissionEntity,
                        AutomationTestEntity, WaveformEntity,
                        SiliconEntity)


def find_project_from_string(project: str):
    project = mongo.db.PROJECT.find_one({"name": project},
                                        {"_id"})
    return project


def save_entity(entity: ENTITY_TYPE):
    return _save_entity(entity._type, entity)


def _save_entity(collection: str, entity: ENTITY_TYPE):
    ''' Inserts a single entity into the database '''
    inserted = mongo.db[collection].insert_one(entity.to_dict())
    return inserted


def save_bulk_entity(entity_list: t.List[Entity]):
    collection = entity_list[0]._type
    return _save_bulk_entity(collection=collection, entity_list=entity_list)


def _save_bulk_entity(collection: str, entity_list: t.List[Entity]):
    '''
    Inserts multiple entities of a single type into the database
    '''
    dict_list = [e.to_dict() for e in entity_list]
    bulk_inserted = mongo.db[collection].insert_many(dict_list)
    return bulk_inserted


def update_entity(entity: ENTITY_TYPE):
    return _update_entity(collection=entity._type, entity=entity)


def _update_entity(collection: str, entity: ENTITY_TYPE):
    '''

    '''
    # TODO:: Actually complete this function
    raise NotImplementedError
    key = {}
    data = {}
    data = {"$set": {"lastModified": datetime.datetime.now()}}
    updated = mongo.db[collection].update(key=key,  # query_parameter,
                                          data=data,  # replacement document
                                          upsert=True,
                                          multi=False
                                          )
    return updated


def create_entity(entity_class: ENTITY_TYPE, adict: dict) -> ENTITY_TYPE:
    new_entity = entity_class.from_dict(adict=adict)
    saved_entity = save_entity(entity=new_entity)
    return saved_entity


def create_project(project: PROJECT_DESCRIPTOR,
                   silicon: LIST_OF_SILICON = list):
    project_dict = {"_id": project,
                    "name": project,
                    "silicon": silicon}
    project = create_entity(entity_class=ProjectEntity, adict=project_dict)
    return project


def create_pba(part_number: str, project: PROJECT_DESCRIPTOR,
               notes: str = "", reworks: t.List[ObjectId] = list,
               customers: list = list) -> PBAEntity:
    pba_dict = {"part_number": part_number,
                "_id": part_number,
                "project": find_project_from_string(project=project),
                "notes": notes,
                "reworks": reworks,
                "customers": customers}
    pba = create_entity(PBAEntity, adict=pba_dict)
    return pba


def create_rework(rework: int, pba: str, notes: str = "",
                  eetrack_id: str = "") -> ReworkEntity:
    rework_dict = {"rework": rework,
                   "pba": pba,
                   "notes": notes,
                   eetrack_id: eetrack_id}
    rework = create_entity(ReworkEntity, adict=rework_dict)
    return rework


def create_silicon(name: str, acronym: str,
                   features: dict = dict) -> SiliconEntity:
    silicon_dict = {"name": name,
                    "acronym": acronym,
                    "features": features}
    silicon = create_entity(SiliconEntity, adict=silicon_dict)
    return silicon


def create_submission(descriptor: str, rework_id: str, pba: str):
    sub_dict = {"submission": descriptor,
                "rework_id": rework_id,
                "pba": pba}

    submission = create_entity(SubmissionEntity, adict=sub_dict)
    return submission


def create_runid(runid: int) -> RunidEntity:
    runid_dict = {"runid": runid}
    runid = create_entity(RunidEntity, adict=runid_dict)
    return runid


def create_automation_test(name: str, notes: str):
    test_dict = {"name": name,
                 "notes": notes}
    test = create_entity(AutomationTestEntity, adict=test_dict)
    return test


def create_datacapture(number: int, runid: int,
                       waveforms: list = list) -> WaveformCaptureEntity:
    capture_dict = {"capture": number,
                    "runid": runid,
                    "waveform_names": waveforms}
    capture = create_entity(WaveformCaptureEntity, adict=capture_dict)
    return capture


def create_waveform(testpoint: str, location: str, scope_channel: str, runid:
int,
                    capture: int, units: str = "V",
                    user_reviewed: bool = False) -> WaveformEntity:
    wf_path = Path(location)
    if not wf_path.exists():
        # TODO:: What do we do if the path isn't real?
        raise NotImplementedError

    steady_state_min = 0
    steady_state_mean = 0
    steady_state_max = 0
    steady_state_pk2pk = 0
    wf_max = 0
    wf_min = 0
    downsample = [1, 2, 3, 4, 5]

    wf_dict = {"testpoint": testpoint,
               "runid": runid,
               "capture": capture,
               "units": units,
               "user_reviewed": user_reviewed,
               "location": location,
               "scope_channel": scope_channel,
               "steady_state_min": steady_state_min,
               "steady_state_max": steady_state_max,
               "steady_state_mean": steady_state_mean,
               "steady_state_pk2pk": steady_state_pk2pk,
               "max": wf_max,
               "min": wf_min,
               "downsample": downsample
               }

    waveform = create_entity(WaveformEntity, adict=wf_dict)
