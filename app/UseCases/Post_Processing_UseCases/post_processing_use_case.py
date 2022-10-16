from __future__ import annotations

import typing as t
from collections import defaultdict, OrderedDict

import pandas as pd
import numpy as np

from pathlib import Path
import os

from app.shared.Entities import *

from app.shared.UseCase.usecase import UseCase
from app.shared.Requests.requests import ValidRequestObject
from app.shared.Responses.response import ResponseSuccess

from app.Repository.repository import Repository
import matplotlib.pyplot as plt

from app import globalConfig

class PostProcessingRequestObject(ValidRequestObject):
    groupby_list: t.List[str]
    df: pd.DataFrame

    def __init__(self, filters: t.List[str], df: pd.DataFrame):
        self.groupby_list = filters
        self.df = df

    @classmethod
    def from_dict(cls, adict) -> PostProcessingRequestObject:
        return cls(**adict)


class PostProcessingUseCase(UseCase):
    repo: Repository
    sheet_name: str
    waveform_test: bool = True

    def __init__(self, repo: Repository):
        self.repo = repo

    def process_request(self, request_object: PostProcessingRequestObject) \
            -> ResponseSuccess:
        result_df = self.post_process(request_object=request_object)

        result_tuple = (self.sheet_name, result_df)

        return ResponseSuccess(value=result_tuple)

    def post_process(self, request_object: PostProcessingRequestObject) -> \
            pd.DataFrame:
        raise NotImplementedError

    def _test_specific_columns(self):
        raise NotImplementedError

    def filter_df(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns a filtered DataFrame.
        :param raw_df: pandas DataFrame to be filtered
        :return: filtered pandas.DataFrame
        """
        test_specific_fields = self._test_specific_columns()

        filter_headers = [
            "dut", "pba", "rework", "serial_number", "runid", "comments",
            "status_json_status", "capture", "location", "testpoint",
            "scope_channel", "product_id", "pba_id", "rework_id",
            "submission_id", "run_id", "automation_id", "datacapture_id",
            "waveform_id", "temperature_power_settings_json_chamber_setpoint",
            "temperature_power_settings_json_power_supply_channels_channel_name_1",
            "temperature_power_settings_json_power_supply_channels_channel_on_1",
            "temperature_power_settings_json_power_supply_channels_group_1",
            "temperature_power_settings_json_power_supply_channels_voltage_setpoint_1",
            "temperature_power_settings_json_power_supply_channels_slew_rate_1",
            "temperature_power_settings_json_power_supply_channels_on_delay_1",
            "temperature_power_settings_json_power_supply_channels_off_delay_1",
            "temperature_power_settings_json_power_supply_channels_channel_name_2",
            "temperature_power_settings_json_power_supply_channels_channel_on_2",
            "temperature_power_settings_json_power_supply_channels_group_2",
            "temperature_power_settings_json_power_supply_channels_voltage_setpoint_2",
            "temperature_power_settings_json_power_supply_channels_slew_rate_2",
            "temperature_power_settings_json_power_supply_channels_on_delay_2",
            "temperature_power_settings_json_power_supply_channels_off_delay_2",
            "temperature_power_settings_json_power_supply_channels_channel_name_3",
            "temperature_power_settings_json_power_supply_channels_channel_on_3",
            "temperature_power_settings_json_power_supply_channels_group_3",
            "temperature_power_settings_json_power_supply_channels_voltage_setpoint_3",
            "temperature_power_settings_json_power_supply_channels_slew_rate_3",
            "temperature_power_settings_json_power_supply_channels_on_delay_3",
            "temperature_power_settings_json_power_supply_channels_off_delay_3",
            "temperature_power_settings_json_power_supply_channels_channel_name_4",
            "temperature_power_settings_json_power_supply_channels_channel_on_4",
            "temperature_power_settings_json_power_supply_channels_group_4",
            "temperature_power_settings_json_power_supply_channels_voltage_setpoint_4",
            "temperature_power_settings_json_power_supply_channels_slew_rate_4",
            "temperature_power_settings_json_power_supply_channels_on_delay_4",
            "temperature_power_settings_json_power_supply_channels_off_delay_4",
            "file_capture_capture.png"
        ]
        filter_headers.extend(test_specific_fields)

        filt_df = raw_df[filter_headers]

        filt_df.rename(columns={"status_json_status": "status",
                                "temperature_power_settings_json_chamber_setpoint": "temperature",
                                "temperature_power_settings_json_power_supply_channels_channel_name_1": "ch1_name",
                                "temperature_power_settings_json_power_supply_channels_channel_on_1": "ch1_on",
                                "temperature_power_settings_json_power_supply_channels_group_1": "ch1_group",
                                "temperature_power_settings_json_power_supply_channels_voltage_setpoint_1": "ch1_setpoint",
                                "temperature_power_settings_json_power_supply_channels_slew_rate_1": "ch1_slew",
                                "temperature_power_settings_json_power_supply_channels_on_delay_1": "ch1_on_delay",
                                "temperature_power_settings_json_power_supply_channels_off_delay_1": "ch1_off_delay",
                                "temperature_power_settings_json_power_supply_channels_channel_name_2": "ch2_name",
                                "temperature_power_settings_json_power_supply_channels_channel_on_2": "ch2_on",
                                "temperature_power_settings_json_power_supply_channels_group_2": "ch2_group",
                                "temperature_power_settings_json_power_supply_channels_voltage_setpoint_2": "ch2_setpoint",
                                "temperature_power_settings_json_power_supply_channels_slew_rate_2": "ch2_slew",
                                "temperature_power_settings_json_power_supply_channels_on_delay_2": "ch2_on_delay",
                                "temperature_power_settings_json_power_supply_channels_off_delay_2": "ch2_off_delay",
                                "temperature_power_settings_json_power_supply_channels_channel_name_3": "ch3_name",
                                "temperature_power_settings_json_power_supply_channels_channel_on_3": "ch3_on",
                                "temperature_power_settings_json_power_supply_channels_group_3": "ch3_group",
                                "temperature_power_settings_json_power_supply_channels_voltage_setpoint_3": "ch3_setpoint",
                                "temperature_power_settings_json_power_supply_channels_slew_rate_3": "ch3_slew",
                                "temperature_power_settings_json_power_supply_channels_on_delay_3": "ch3_on_delay",
                                "temperature_power_settings_json_power_supply_channels_off_delay_3": "ch3_off_delay",
                                "temperature_power_settings_json_power_supply_channels_channel_name_4": "ch4_name",
                                "temperature_power_settings_json_power_supply_channels_channel_on_4": "ch4_on",
                                "temperature_power_settings_json_power_supply_channels_group_4": "ch4_group",
                                "temperature_power_settings_json_power_supply_channels_voltage_setpoint_4": "ch4_setpoint",
                                "temperature_power_settings_json_power_supply_channels_slew_rate_4": "ch4_slew",
                                "temperature_power_settings_json_power_supply_channels_on_delay_4": "ch4_on_delay",
                                "temperature_power_settings_json_power_supply_channels_off_delay_4": "ch4_off_delay",
                                "file_capture_capture.png": "capture_png"
                                }, inplace=True)

        return filt_df

    def get_unique_slew_rates(self, input_df: pd.DataFrame) -> t.List[int]:
        slew_rates = ["ch1_slew", "ch2_slew", "ch3_slew", "ch4_slew"]
        channels = ["ch1_group", "ch2_group", "ch3_group", "ch4_group"]
        cheese = input_df.melt(id_vars=channels, value_vars=slew_rates)
        unique_slewrates = cheese.value.unique()
        return list(unique_slewrates)

    def filter_df_by_slewrate(self, filtered_df: pd.DataFrame, slew_rate: int,
                              group: str = "Main"):
        assert group in ["Main", "Aux"], f"filter group [{group}] must be " \
                                         "either 'Main' or 'Aux'"
        group_chs = []
        filters = []
        for ch in range(1, 5):
            ch_group = f"ch{ch}_group"
            if group in filtered_df[ch_group].values:
                ch_slew = f"ch{ch}_slew"
                filt_df = filtered_df[(filtered_df[ch_slew] == slew_rate)]
                filters.append(filt_df)

        if not len(filters):
            return pd.DataFrame()
        else:
            return pd.concat(filters)

    def _get_entity_order(self) -> t.List[None]:
        '''
        @return: Essentially just returns a list of "None"
        '''
        project_entity = None
        pba_entity = None
        rework_entity = None
        submission_entity = None
        runid_entity = None
        automation_entity = None
        capture_entity = None
        entities = [project_entity, pba_entity, rework_entity,
                    submission_entity, runid_entity, automation_entity,
                    capture_entity]
        if self.waveform_test:
            waveform_entity = None
            entities.append(waveform_entity)
        return entities

    def _get_database_query_functions(self) -> t.List:
        query_functs = [self.query_projects, self.query_pbas,
                        self.query_reworks, self.query_submissions,
                        self.query_runids, self.query_automation_tests]
        if self.waveform_test:
            query_functs.append(self.query_waveform_captures)
            query_functs.append(self.query_waveforms)
        else:
            query_functs.append(self.query_traffic_captures)
        return query_functs

    def _get_id_dataframe_headers(self) -> t.List[str]:
        header_ids = ["product_id", "pba_id", "rework_id", "submission_id",
                      "run_id", "automation_id", "datacapture_id"]
        if self.waveform_test:
            header_ids.append("waveform_id")
        return header_ids

    def business_logic(self, **kwargs) -> OrderedDict:
        """
        Test specific Pass/Fail criteria goes here

        @param kwargs:
        @return:
        """
        raise NotImplementedError

    def make_results_df2(self, filtered_df: pd.DataFrame,
                         merge_columns: t.List[str]) -> pd.DataFrame:
        """

        @param filtered_df:
        @param merge_rows:
        @return:
        """
        entities = self._get_entity_order()
        query_functs = self._get_database_query_functions()
        header_ids = self._get_id_dataframe_headers()

        # Do not find entities for merge columns.
        # The test will probably be doing something else with those...
        for merge_header in merge_columns:
            if merge_header in header_ids:
                index = header_ids.index(merge_header)
                header_ids.pop(index)
                entities.pop(index)
                query_functs.pop(index)

        result_df = pd.DataFrame()
        for i, row in filtered_df.iterrows():
            result_row = OrderedDict()
            for entity, query_funct, header_id in zip(entities, query_functs,
                                                      header_ids):
                # Grab the entity
                update = False
                if entity is None:
                    update = True
                elif entity._id != row[header_id]:
                    update = True

                if update:
                    index = entities.index(entity)
                    # print(header_id, row_dict[header_id])
                    entity = query_funct(filters={"_id":
                                                      str(row[header_id])})[0]
                    entities[index] = entity

                result_row.update(entity.to_result())

            row_df = self.business_logic(
                result_row=result_row,
                confidence_level=row.target_confidence,
                specified_ber=row.specified_ber,
                ethagent_capture=entity)
            result_df = pd.concat([row_df, result_df], ignore_index=True)
        return result_df

    def make_results_df(self, filtered_df: pd.DataFrame,
                        merge_columns: t.List[str]) -> pd.DataFrame:
        """

        @param filtered_df:
        @param merge_rows:
        @return:
        """
        entities = self._get_entity_order()
        query_functs = self._get_database_query_functions()
        header_ids = self._get_id_dataframe_headers()

        # Do not find entities for merge columns.
        # The test will probably be doing something else with those...
        for merge_header in merge_columns:
            if merge_header in header_ids:
                index = header_ids.index(merge_header)
                header_ids.pop(index)
                entities.pop(index)
                query_functs.pop(index)

        result_df = pd.DataFrame()
        for i, row in filtered_df.iterrows():
            result_row = OrderedDict()
            for entity, query_funct, header_id in zip(entities, query_functs,
                                                      header_ids):
                # Grab the entity
                update = False
                if entity is None:
                    update = True
                elif entity._id != row[header_id]:
                    update = True

                if update:
                    index = entities.index(entity)
                    # print(header_id, row_dict[header_id])
                    entity = query_funct(filters={"_id":
                                                      str(row[header_id])})[0]
                    entities[index] = entity

                result_row.update(entity.to_result())
            result_row.update(row[merge_columns])
            columns = list(result_row.keys())
            row_df = pd.DataFrame(data=result_row, index=[i],
                                  columns=columns)
            result_df = pd.concat([row_df, result_df])
        return result_df

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

    def get_main_slew_rates(self, filtered_df: pd.DataFrame):
        group_key = "Main"
        return self._voltage_group_filter(group=group_key,
                                          header_fmt="ch{}_slew",
                                          filtered_df=filtered_df)

    def _voltage_group_filter(self, group: str, filtered_df: pd.DataFrame,
                              header_fmt: str) -> t.List:
        result = set()
        for ch in range(1, 5):
            group_header = f"ch{ch}_group"
            ch_df = filtered_df[filtered_df[group_header] == group]
            if not ch_df.empty:
                header = header_fmt.format(ch)
                ch_results = ch_df[header].unique()
                result.update(ch_results)
        return list(result)

    def get_unique_temperatures(self, filtered_df: pd.DataFrame) -> t.List[int]:
        temperatures = filtered_df['temperature'].unique()
        return list(temperatures)

    def get_main_voltages(self, filtered_df: pd.DataFrame) -> t.List[float]:
        group_key = "Main"
        return self._voltage_group_filter(group=group_key,
                                          header_fmt="ch{}_setpoint",
                                          filtered_df=filtered_df)

    def get_aux_voltages(self, filtered_df: pd.DataFrame) -> t.List[float]:
        group_key = "Aux"
        header_fmt = "ch{}_setpoint"
        return self._voltage_group_filter(group=group_key,
                                          header_fmt=header_fmt,
                                          filtered_df=filtered_df)

    #def check_if_current_waveform(self, waveform: WaveformEntity) -> bool:
    #    if waveform

    def waveform_list_minimum_steady_state_index(self, waveform_list: t.List[
        WaveformEntity]) -> int:

        index_list = []
        for wf in waveform_list:
            if wf.units == "A":
                continue  ## Steady State Index is not set for current rails,
                # will return 0
            index_list.append(wf.steady_state_index())
        return min(index_list)

    def waveform_list_minimum_ramp_index(self, waveform_list: t.List[
        WaveformEntity]) -> int:
        raise NotImplementedError
        # TODO:: Need waveform function that finds when ramp starts
        '''
        index_list = []
        for wf in waveform_list:
            if wf.units == "A":
                continue  ## Steady State Index is not set for current rails,
                # will return 0
            index_list.append(wf.ramp_index())
        return min(index_list)
        '''

    def load_waveforms_by_df(self, df: pd.DataFrame) -> t.List[WaveformEntity]:
        wf_ids = df["waveform_id"].values
        filter_list = [{"_id": id} for id in wf_ids]
        wf_dicts = self.repo.find_many_waveforms(list_of_filters=filter_list)
        wf_entities = [WaveformEntity.from_dict(wf_dict) for wf_dict in
                       wf_dicts]
        return wf_entities

    def load_waveforms_dict(self, df: pd.DataFrame) -> t.Dict[str, t.List[
        WaveformEntity]]:
        wfs = self.load_waveforms_by_df(df=df)

        wf_dict = defaultdict(list)

        for waveform in wfs:
            wf_dict[waveform.testpoint].append(waveform)

        return wf_dict

    def _convert_seconds_to_milliseconds(self, seconds: float) -> float:
        return seconds * 1000

    def return_wf(self, waveform_id) -> WaveformEntity:
        wf_dict = self.repo.find_waveform_by_id(waveform_id=waveform_id)
        wf = WaveformEntity.from_dict(wf_dict)
        return wf

    def return_edge_rail_pairs(self, waveform_list: t.List[WaveformEntity]) -> \
            t.List[t.Tuple[WaveformEntity, WaveformEntity]]:
        edges = [wf for wf in waveform_list if wf.edge]
        return self._pair_voltage_to_current(edges=edges)

    def return_edge_rail_pairs_df(self, df: pd.DataFrame) -> t.List[
        t.Tuple[WaveformEntity, WaveformEntity]]:
        ''' Takes in a dataframe and turns it into edge wf tuples '''

        edges = self._return_edge_waveforms(df=df)
        return self._pair_voltage_to_current(edges=edges)

    def _row_from_waveform_id(self, df: pd.DataFrame,
                              waveform_id: str) -> pd.Series:
        row = df[df.waveform_id == waveform_id]
        if not row.empty:
            return row.iloc[0]
        else:
            row = pd.Series()
            return row

    def _waveform_id_from_row(self, df_row: pd.Series) -> str:
        wf_id = df_row["waveform_id"]
        return wf_id

    def _spec_max_from_waveform_id(self, df: pd.DataFrame, waveform_id: str):
        wf_df = df[df["waveform_id"] == waveform_id]
        spec = wf_df.iloc[0]["spec_max"]
        return spec

    def _spec_max_from_row(self, df_row: pd.Series) -> float:
        spec = df_row['spec_max']
        return spec

    def _max_power_from_row(self, df_row: pd.Series) -> float:
        spec = df_row['max_power']
        return spec

    def _spec_min_from_row(self, df_row: pd.Series) -> float:
        spec = df_row['spec_min']
        return spec

    def _expected_nominal_from_row(self, df_row: pd.Series) -> float:
        spec = df_row['expected_nominal']
        return spec

    def _return_rails_by_edge(self, df: pd.DataFrame,
                              edge: bool = False) -> list:
        rails = []
        for i, row in df[df['edge_rail'] == edge].iterrows():
            wf_id = row['waveform_id']
            wf = self.return_wf(waveform_id=wf_id)
            rails.append(wf)
        return rails

    def _return_rails(self, df: pd.DataFrame) -> t.List[WaveformEntity]:
        wf_ids = df["WaveformEntity_id"].values
        filters = [{"_id": wf_id} for wf_id in wf_ids]
        rails = self.repo.find_many_waveforms(filters=filters)
        wfs = [WaveformEntity.from_dict(adict=wf_dict) for wf_dict in rails]
        return wfs

    @classmethod
    def _create_fake_edge_rail(cls, testpoint: str, runid: int, capture: int,
                               test_category: str, downsample: list,
                               associated_rail: str, units: str = "V",
                               location: str = "N/A", scope_channel=99) \
            -> WaveformEntity:
        v_wf = WaveformEntity(testpoint=testpoint,
                              runid=runid,
                              capture=capture,
                              test_category=test_category,
                              units=units,
                              location=location, scope_channel=scope_channel,
                              downsample=downsample,
                              edge=True, associated_rail=associated_rail)
        return v_wf

    @classmethod
    def _pair_voltage_to_current(cls, edges: t.List[WaveformEntity]) -> \
            t.List[t.Tuple[WaveformEntity, WaveformEntity]]:
        '''
        Returns a list of tuples containing (voltage, current) waveform_names.
        '''
        volt_list = [wf for wf in edges if wf.units == "V"]
        current_list = [wf for wf in edges if wf.units == "A"]
        result = []
        for c_wf in current_list:
            v_wf = [v for v in volt_list if v.testpoint == c_wf.associated_rail]
            if not v_wf:
                v_wf = cls._fake_rail_from_current(current_rail=c_wf)
            else:
                v_wf = v_wf[0]

            result.append((v_wf, c_wf))

        return result

    def _return_onboard_rails(self, df: pd.DataFrame) -> list:
        edge = False
        return self._return_rails_by_edge(df, edge)

    def _return_edge_waveforms(self, df: pd.DataFrame) -> list:
        edge = True
        return self._return_rails_by_edge(df, edge)

    @classmethod
    def _fake_rail_from_current(cls,
                                current_rail: WaveformEntity) \
            -> WaveformEntity:
        testpoint = f"{current_rail.testpoint} Missing Voltage Rail"
        downsample_x = current_rail.downsample[0]
        downsample_y = np.zeros(len(downsample_x)).tolist()
        downsample = [downsample_x, downsample_y]

        fake = cls._create_fake_edge_rail(testpoint=testpoint,
                                          runid=current_rail.runid,
                                          capture=current_rail.capture,
                                          test_category=current_rail.test_category,
                                          downsample=downsample,
                                          associated_rail=current_rail.testpoint)
        return fake

    def make_plot(self, **kwargs) -> plt.Figure:
        raise NotImplementedError

    def set_axes_labels(self, ax: plt.Subplot, xlabel: str = "Time (ms)",
                        ylabel: str = "Voltage (V)") -> None:

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

    def axes_vertical_line(self, ax: plt.Subplot, xloc: int, label: str,
                           ymax: int, ymin: int = 0) -> None:
        COLOR = "black"

        ax.axvline(x=xloc, ymin=ymin, ymax=ymax, c=COLOR)
        ax.text(xloc, 0, label, rotation=90, c=COLOR)

    def axes_add_max_min(self, ax: plt.Subplot, spec_min: float,
                         spec_max: float, x_end: int, x_start: int = 0) -> None:
        assert spec_max > spec_min, "spec_max must be greater than spec_min: " \
                                    f"{spec_max} >= {spec_min}"
        # CAN USE THESE TERMS TO BETTER SPACE MAX/MIN SPEC TEXT IN THE FUTURE
        # MIN_SPACING = 0.05  # (spec_max-spec_min)/4
        # MAX_SPACING = 0.01
        # ylim = ax.get_ylim()
        COLOR = 'r'
        xlim = ax.get_xlim()

        # spec max
        ax.axhline(y=spec_max, xmax=x_end, xmin=x_start)
        ax.text(xlim[0], spec_max, "Spec Max", c=COLOR)

        # spec min
        ax.axhline(y=spec_min, xmax=x_end, xmin=x_start, c=COLOR)
        ax.text(xlim[0], spec_min, "Spec Min", c=COLOR)

    def axes_add_y_tick(self, ax: plt.Subplot, nominal_value: float,
                        label: str = ""):
        COLOR = "purple"

        xlim = ax.get_xlim()
        xsize = xlim[1] - xlim[0]
        text_x = xsize // 40 + 0.5

        label_text = f"{round(nominal_value, 2)}"
        if label:
            label_text = f"{label}: {label_text}"

        # xmin/xmax are percentages of graph covered
        ax.axhline(y=nominal_value, xmin=0, xmax=0.01, c=COLOR)

        ax.text(xlim[0] - text_x, nominal_value, label_text,
                c=COLOR)

    def save_testpoint_plot(self, result_dict: OrderedDict, fig: plt.Figure,
                            waveform_entity: WaveformEntity) -> Path:
        filename = self.make_testpoint_filename(result_dict=result_dict,
                                                wf_entity=waveform_entity)
        saved_path = self.save_plot(result_dict=result_dict, fig=fig,
                                    filename=filename, suffix=".png")
        return saved_path

    def save_plot(self, result_dict: OrderedDict, fig: plt.Figure,
                  filename: str, suffix: str = ".png"):
        save_path = self.make_save_path(filename=filename,
                                        result_dict=result_dict)
        save_path = save_path.with_suffix(suffix=suffix)

        self._save_plot(save_path=save_path, fig=fig)
        return save_path

    def _save_plot(self, save_path: str, fig: plt.Figure):
        fig.savefig(fname=save_path, dpi=200, format="png")
        plt.close(fig)

    def make_testpoint_filename(self, result_dict: OrderedDict, wf_entity:
    WaveformEntity) -> str:
        return f"{wf_entity.testpoint}-CH{wf_entity.scope_channel}.png"

    def make_save_path(self, filename: str, result_dict: OrderedDict):
        # save_path = Path(Config.RESULTS_FOLDER)
        save_path = Path(r"C:\Users\ammonk\OneDrive - Intel "
                         r"Corporation\Desktop\Test_Folder\fake_uploads\fake_results")
        save_keys = ["DUT", "PBA", "Rework", "DUT Serial", "Runid", "Capture"]

        for key in save_keys:
            path_loc = result_dict.get(key, None)
            if path_loc == None:
                break
            else:
                save_path = save_path.joinpath(str(path_loc))

        if not save_path.exists():
            save_path.mkdir(parents=True)

        save_path = save_path.joinpath(filename)
        return save_path
