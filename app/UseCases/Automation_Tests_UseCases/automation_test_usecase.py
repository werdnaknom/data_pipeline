from __future__ import annotations

import typing as t
from pathlib import Path
import platform
import time
import datetime as dt
import os
from collections import OrderedDict

import celery
import pandas as pd

from app.shared.Responses.response import ResponseSuccess, Response
from app.shared.UseCase.usecase import UseCase
from app.shared.Entities import *
from app.UseCases.Entity_Uploading.analyze_waveform_usecase import \
    AnalyzeWaveformRequestObject, AnalyzeWaveformUseCase
from app.shared.Requests.requests import ValidRequestObject
from app.Repository.repository import Repository


def timing_val(funct):
    def wrapper(*args, **kwargs):
        t1 = time.time()
        res = funct(*args, **kwargs)
        t2 = time.time()
        timer = t2 - t1
        print(f"{funct.__name__}: {timer}")
        return res

    return wrapper


class AutomationTestRequestObject(ValidRequestObject):
    df: pd.DataFrame
    filter_by: str

    def __init__(self, df: pd.DataFrame, filter_by: str = "default"):
        assert isinstance(df, pd.DataFrame)
        self.df = df
        self.filter_by = filter_by

    @classmethod
    def from_dict(cls, adict) -> AutomationTestRequestObject:
        return cls(**adict)


class AutomationTestUseCase(UseCase):
    _name = "AutomationTest"
    LAST_FILTERBY: str = None
    repo: Repository

    def __init__(self, repo: Repository):
        self.repo = repo

    def format_filename(self):
        time_str = dt.datetime.now().strftime("%h-%d_%H%M%S")
        return f"{self._name}_{time_str}.xlsx"

    def set_filter_by_list(self, filter_by: str, what_default: str = "capture") \
            -> t.List[str]:
        l = []
        if filter_by == "default":
            filter_by = what_default

        if filter_by == "testpoint":
            return self._filterby_testpoint()
        elif filter_by == "capture":
            return self._filterby_capture()
        elif filter_by == "runid":
            return self._filterby_runid()
        elif filter_by == "sample":
            return self._filterby_sample()
        elif filter_by == "rework":
            return self._filterby_rework()
        elif filter_by == "pba":
            return self._filterby_pba()
        elif filter_by == "dut":
            return self._filterby_dut()
        raise AttributeError(f"{filter_by} is not a valid filterby string")

    def _filterby_testpoint(self) -> t.List[str]:
        raise NotImplementedError("filterby Testpoint not implemented")

    def _add_filterby(self, previous: t.List[str], add: str) -> t.List[str]:
        last = previous.pop(len(previous) - 1)
        filterby = previous + [add, last]
        return filterby

    def _filterby_dut(self) -> t.List[str]:
        return ["product_id", self.LAST_FILTERBY]

    def _filterby_pba(self) -> t.List[str]:
        return self._add_filterby(previous=self._filterby_dut(), add="pba_id")

    def _filterby_rework(self) -> t.List[str]:
        return self._add_filterby(previous=self._filterby_pba(),
                                  add="rework_id")

    def _filterby_sample(self) -> t.List[str]:
        return self._add_filterby(previous=self._filterby_rework(),
                                  add="submission_id")

    def _filterby_runid(self) -> t.List[str]:
        return self._add_filterby(previous=self._filterby_sample(),
                                  add="run_id")

    def _filterby_capture(self) -> t.List[str]:
        return self._add_filterby(previous=self._filterby_runid(),
                                  add="datacapture_id")

    def make_filter_dict(self, filter_by: t.List[str],
                         filter_tuple: t.Tuple[str]):
        if isinstance(filter_tuple, str):
            filter_dict = {filter_by[0]: filter_tuple}
        else:
            filter_dict = {}
            for filt, value in zip(filter_by, filter_tuple):
                filter_dict[filt] = value

        return filter_dict

    def update_filter_entities(self, new_dict: t.OrderedDict[str, str],
                               old_dict: t.OrderedDict[str, str]):
        for key, new_value in new_dict.items():
            old_entity = old_dict.get(key, None)
            if old_entity != None:
                old_value = old_entity._id
            else:
                old_value = None

            # Replace the old entity if needed
            if (old_value == None) or (str(old_value) != str(new_value)):
                new_entity = self.query_id(key=key, id=new_value)
                new_dict[key] = new_entity
            else:
                new_dict[key] = old_entity

        return new_dict

    def group_filter(self, filter_by: t.List[str],
                     df: pd.DataFrame) -> t.List[dict]:
        """
        Takes in a dataframe and groupby_list it by the filter_by list.
        Returns a list of dictionaries with key/value pairs of the groupby_list used
        and the filtered dataframe.

        @param filter_by:  List of groupby_list to apply to the dataframe
        @param df: Data dataframe
        @return: List[Dict(Filter = Value,
                           Filter = Value,etc...
                           df = filtered_dataframe)]
        """
        result_list = []

        filter_groups = df.groupby(by=filter_by)
        for filters, group_df in filter_groups:
            results_dict = {}
            for key, value in zip(filter_by, filters):
                results_dict[key] = value
            results_dict["df"] = group_df
            result_list.append(results_dict)
        return result_list

    def build_excel_file(self,
                         data_dict: t.OrderedDict[str, pd.DataFrame]) -> Path:
        filename = self.format_filename()
        results_folder = self.get_result_directory()
        output_path = Path(results_folder).joinpath(filename)
        # output_path = Path(os.environ.get("RESULTS_FOLDER")).joinpath(filename)

        output_path = self._build_excel_file(output_path=output_path,
                                             data_dict=data_dict)

        return output_path

    def _build_excel_file(self, output_path: Path,
                          data_dict: t.OrderedDict[str, pd.DataFrame]) -> str:
        """

        @param output_path:  pd.ExcelWriter
        @return: path to excel writer

        """
        raise NotImplementedError

    def query_id(self, key: str, id: str) -> Entity:
        filter = {"_id": str(id)}
        result = []
        if key == "product_id":
            result = self.query_projects(filters=filter)
        elif key == "pba_id":
            result = self.query_pbas(filters=filter)
        elif key == "rework_id":
            result = self.query_reworks(filters=filter)
        elif key == "submission_id":
            result = self.query_submissions(filters=filter)
        elif key == "run_id":
            result = self.query_runids(filters=filter)
        elif key == "datacapture_id":
            if "waveform" in id:
                result = self.query_waveform_captures(filters=filter)
            else:
                result = self.query_traffic_captures(filters=filter)
        if result:
            return result[0]
        else:
            return None

    def query_projects(self, filters: dict) -> t.List[ProjectEntity]:
        list_dict = self.repo.query_projects(filters=filters)
        entity_list = [ProjectEntity.from_dict(adict=adict) for adict in
                       list_dict]
        return entity_list

    def query_pbas(self, filters: dict) -> t.List[PBAEntity]:
        list_dict = self.repo.query_pbas(filters=filters)
        entity_list = [PBAEntity.from_dict(adict=adict) for adict in
                       list_dict]
        return entity_list

    def query_reworks(self, filters: dict) -> t.List[ReworkEntity]:
        list_dict = self.repo.query_reworks(filters=filters)
        entity_list = [ReworkEntity.from_dict(adict=adict) for adict in
                       list_dict]
        return entity_list

    def query_submissions(self, filters: dict) -> t.List[SubmissionEntity]:
        list_dict = self.repo.query_submissions(filters=filters)
        entity_list = [SubmissionEntity.from_dict(adict=adict) for adict in
                       list_dict]
        return entity_list

    def query_runids(self, filters: dict) -> t.List[RunidEntity]:
        list_dict = self.repo.query_runids(filters=filters)
        entity_list = [RunidEntity.from_dict(adict=adict) for adict in
                       list_dict]
        return entity_list

    def query_automation_tests(self, filters: dict) -> t.List[
        AutomationTestEntity]:
        list_dict = self.repo.query_automation_tests(filters=filters)
        entity_list = [AutomationTestEntity.from_dict(adict=adict) for adict in
                       list_dict]
        return entity_list

    def query_waveform_captures(self, filters: dict) -> t.List[
        WaveformCaptureEntity]:
        list_dict = self.repo.query_waveform_captures(filters=filters)
        entity_list = [WaveformCaptureEntity.from_dict(adict=adict) for adict in
                       list_dict]
        return entity_list

    def query_traffic_captures(self, filters: dict) -> t.List[
        EthAgentCaptureEntity]:
        list_dict = self.repo.query_traffic_captures(filters=filters)
        entity_list = [EthAgentCaptureEntity.from_dict(adict=adict) for adict
                       in list_dict]
        return entity_list

    def query_waveforms(self, filters: dict) -> t.List[WaveformEntity]:
        list_dict = self.repo.query_waveforms(filters=filters)
        entity_list = [WaveformEntity.from_dict(adict=adict) for adict in
                       list_dict]
        return entity_list

    def process_filter_entities(self, filter_tuple: t.Tuple[str],
                                groupby_list: t.List[str],
                                entity_dict: t.OrderedDict[str, Entity] = None):
        '''

        @param filter_tuple:  tuple of entity IDs
        @param groupby_list:  List of keys to the entity IDS
        @param entity_dict: Dict of groupby_list keys to Entity objects
        @return: entity_dict -> List of entities
        '''
        # if self.LAST_FILTERBY in groupby_list:
        #    filter_tuple = filter_tuple[:-1]
        #    groupby_list = groupby_list[:-1]

        if entity_dict is None:
            entity_dict = OrderedDict()

        # Filter dict is in format {entity_key: entity_id}
        filter_dict = self.make_filter_dict(filter_by=groupby_list,
                                            filter_tuple=filter_tuple)
        # Turn those entity_ids into actual entity objets
        filter_entities = self.update_filter_entities(
            new_dict=filter_dict, old_dict=entity_dict)

        return filter_entities

    def combine_filters_with_results(self, entity_dict: t.OrderedDict,
                                     feature_dict: t.OrderedDict,
                                     response: ResponseSuccess) -> pd.DataFrame:
        if response:  # Response Success == True
            resp_df = response.value
            if resp_df.empty:
                return resp_df
        else:
            resp_df = pd.DataFrame({"Test Failure": response.message})

        result_dict = OrderedDict()
        for entity in entity_dict.values():
            result_dict.update(entity.to_result())

        result_dict.update(feature_dict)

        result_df = pd.DataFrame(result_dict, columns=list(result_dict.keys()),
                                 index=[0])
        result_df = pd.concat([result_df, resp_df], axis=1)
        return result_df
