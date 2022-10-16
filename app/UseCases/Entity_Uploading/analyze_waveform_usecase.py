from pathlib import Path

import pandas as pd
import numpy as np

from app.Repository.repository import Repository
from app.shared.UseCase.usecase import UseCase
from app.shared.Responses.response import Response, ResponseSuccess
from app.shared.Requests.requests import ValidRequestObject
from app.shared.Entities.entities import WaveformEntity, TriStateType

from app.shared.Helpers.waveform_functions import read_waveform_binary, \
    create_waveform_x_coords, min_max_downsample_2d, \
    find_steady_state_waveform_by_percentile

MIN_MAX_BIN_SIZE = 1000


class AnalyzeWaveformRequestObject(ValidRequestObject):
    def __init__(self, df_row: pd.Series):
        self.testpoint = self._get_testpoint(df_row)
        self.test_category = self._get_test_category(df_row)
        self.capture = self._get_capture(df_row)
        self.runid = self._get_runid(df_row)
        self.scope_channel: int = self._get_scope_channel(df_row)
        self.location: str = self._get_location(df_row)
        self.initial_x: float = self._get_initial_x(df_row)
        self.x_increment: float = self._get_x_increment(df_row)
        self.edge: TriStateType = self._get_edge(df_row)
        self.associated_rail: str = self._get_associated_rail(df_row)
        self.compress: bool = self._get_compressed(df_row)
        self.probe_info: dict = self._get_probe_info(df_row, self.scope_channel)
        self.units: str = self.probe_info["units"]
        self.bandwidth: str = self._get_waveform_bandwidth(df_row)

    @classmethod
    def _get_waveform_bandwidth(cls, df_row):
        return "FULL"

    @classmethod
    def _get_edge(cls, df_row: pd.Series) -> TriStateType:
        return df_row.get('edge_rail', None)

    @classmethod
    def _get_associated_rail(cls, df_row: pd.Series) -> str:
        return df_row.get('associated_rail', "")

    @classmethod
    def _get_scope_channel(cls, df_row: pd.Series) -> int:
        return df_row['scope_channel']

    @classmethod
    def _get_test_category(cls, df_row: pd.Series) -> str:
        return df_row['test_category']

    @classmethod
    def _get_location(cls, df_row: pd.Series) -> str:
        return df_row['location']

    @classmethod
    def _get_probe_info(cls, df_row: pd.Series, scope_channel: int) -> dict:
        scope_channel = int(scope_channel)
        ROW_FMT = "system_info_json_probes_{info}_{channel}"
        probe_info = {
            "type": df_row[ROW_FMT.format(info="type",
                                          channel=scope_channel)],
            "serial_number": df_row[ROW_FMT.format(info="serial_number",
                                                   channel=scope_channel)],
            "units": df_row[ROW_FMT.format(info="units",
                                           channel=scope_channel)],
            "cal_status": df_row[ROW_FMT.format(info="cal_status",
                                                channel=scope_channel)],
        }
        return probe_info

    @classmethod
    def _get_testpoint(cls, df_row: pd.Series) -> str:
        return df_row['testpoint']

    @classmethod
    def _get_initial_x(cls, df_row: pd.Series) -> float:

        init_x = df_row['capture_json_initial_x']
        return init_x

    @classmethod
    def _get_x_increment(cls, df_row: pd.Series) -> float:
        return df_row['capture_json_x_increment']

    @classmethod
    def _get_compressed(cls, df_row: pd.Series) -> bool:
        compress = df_row['capture_json_compress']
        if compress == "TRUE":
            return True
        else:
            return False

    @classmethod
    def _get_capture(cls, df_row: pd.Series) -> int:
        return df_row['capture']

    @classmethod
    def _get_runid(cls, df_row: pd.Series) -> int:
        return df_row['runid']


class AnalyzeWaveformUseCase(UseCase):

    def __init__(self, repo: Repository):
        self.repo = repo

    def process_request(self, request_object: AnalyzeWaveformRequestObject) \
            -> Response:
        waveform = self.get_waveform_entity(request_object=request_object)
        return ResponseSuccess(value=waveform)

    def get_waveform_entity(self, request_object: AnalyzeWaveformRequestObject) \
            -> str:  # Returns the WF ID
        exists = self.repo.find_waveform_id(testpoint=request_object.testpoint,
                                            capture=request_object.capture,
                                            runid=request_object.runid,
                                            test_category=request_object.test_category,
                                            scope_channel=request_object.scope_channel)
        if exists:
            return exists
        waveform = self.create_waveform_entity(
            request_object=request_object)
        inserted = self.repo.insert_waveform(entity=waveform)

        return inserted

    def create_waveform_entity(self, request_object:
    AnalyzeWaveformRequestObject) -> WaveformEntity:
        if request_object.units == "A":
            return self.create_current_waveform(request_object)
        else:
            return self.create_voltage_waveform(request_object)

    def create_voltage_waveform(self, request_object:
    AnalyzeWaveformRequestObject):
        wf_location = Path(request_object.location)
        raw_y_wf = read_waveform_binary(location=wf_location,
                                        compressed=request_object.compress)
        raw_x_wf = create_waveform_x_coords(
            x_increment=request_object.x_increment,
            length=raw_y_wf.shape[0])

        wf_max = raw_y_wf.max()
        wf_min = raw_y_wf.min()

        # use default percentile and accuracy
        wf_ss = find_steady_state_waveform_by_percentile(wf=raw_y_wf)
        ss_max = wf_ss.max()
        ss_min = wf_ss.min()
        ss_mean = wf_ss.mean()
        ss_pk2pk = wf_ss.ptp()

        wf_downsample = min_max_downsample_2d(wf_x=raw_x_wf, wf_y=raw_y_wf,
                                              size=MIN_MAX_BIN_SIZE)
        wf_entity = WaveformEntity(testpoint=request_object.testpoint,
                                   runid=request_object.runid,
                                   capture=request_object.capture,
                                   test_category=request_object.test_category,
                                   units=request_object.units,
                                   location=request_object.location,
                                   scope_channel=request_object.scope_channel,
                                   steady_state_min=ss_min,
                                   steady_state_mean=ss_mean,
                                   steady_state_max=ss_max,
                                   steady_state_pk2pk=ss_pk2pk,
                                   edge=request_object.edge,
                                   associated_rail=request_object.associated_rail,
                                   min=wf_min,
                                   max=wf_max,
                                   user_reviewed=False,
                                   downsample=wf_downsample,
                                   )
        return wf_entity

    def create_current_waveform(self,
                                request_object: AnalyzeWaveformRequestObject):
        wf_location = Path(request_object.location)
        raw_y_wf = read_waveform_binary(location=wf_location,
                                        compressed=request_object.compress)
        raw_x_wf = create_waveform_x_coords(
            x_increment=request_object.x_increment,
            length=raw_y_wf.shape[0])

        wf_downsample = min_max_downsample_2d(wf_x=raw_x_wf, wf_y=raw_y_wf,
                                              size=MIN_MAX_BIN_SIZE)

        wf_entity = WaveformEntity(testpoint=request_object.testpoint,
                                   runid=request_object.runid,
                                   capture=request_object.capture,
                                   test_category=request_object.test_category,
                                   units=request_object.units,
                                   location=request_object.location,
                                   scope_channel=request_object.scope_channel,
                                   associated_rail=request_object.associated_rail,
                                   edge=request_object.edge,
                                   max=raw_y_wf.max(),
                                   min=raw_y_wf.min(),
                                   user_reviewed=False,
                                   downsample=wf_downsample
                                   )
        return wf_entity
