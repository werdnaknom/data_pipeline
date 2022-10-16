from __future__ import annotations
import typing as t
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from app.shared.Requests.requests import ValidRequestObject
from app.shared.Responses.response import ResponseSuccess
from app.shared.UseCase.usecase import UseCase
from app.Repository.repository import Repository, MongoRepository

from app.shared.Entities import WaveformEntity

from app import globalConfig


class CapturePostProcessingRequestObject(ValidRequestObject):
    BASE_PATH = Path(globalConfig.RESULTS_FOLDER)

    @classmethod
    def from_dict(cls, adict) -> CapturePostProcessingRequestObject:
        return cls(**adict)

    def make_save_path(self, filter_tuple: t.Tuple[str], testname: str = "") -> \
            Path:
        path = self.BASE_PATH
        for key in filter_tuple:
            path = path.joinpath(str(key))

        if not path.exists():
            path.mkdir(parents=True)  # make parents too if they do not exist

        plot_filename = self.capture_filename(filter_tuple=filter_tuple,
                                              testname=testname)
        save_plot = path.joinpath(plot_filename)
        return save_plot

    def capture_filename(self, filter_tuple: t.Tuple[str], testname: str = ""):
        tuple_names = "_".join(filter_tuple)
        if testname:
            filename = f"{testname}_{tuple_names}"
        else:
            filename = tuple_names
        filename = filename + ".png"
        return filename


class CapturePostProcessorUseCase(UseCase):
    repo: Repository
    sheet_name: str
    waveform_test: bool = True

    def __init__(self, repo: Repository):
        self.repo = repo

    def process_request(self,
                        request_object: CapturePostProcessingRequestObject) \
            -> ResponseSuccess:
        result_df = self.post_process(request_object=request_object)

        return ResponseSuccess(value=result_df)

    def post_process(self,
                     request_object: CapturePostProcessingRequestObject) \
            -> pd.DataFrame:
        raise NotImplementedError

    def load_waveforms_by_df(self, df:pd.DataFrame) -> t.List[WaveformEntity]:
        wf_ids = df["waveform_id"].values
        filter_list = [{"_id": id} for id in wf_ids]
        wf_dicts = self.repo.find_many_waveforms(list_of_filters=filter_list)
        wf_entities = [WaveformEntity.from_dict(wf_dict) for wf_dict in
                       wf_dicts]
        return wf_entities

    def load_waveforms(self, waveform_ids: t.List[str]) \
            -> t.List[WaveformEntity]:
        filter_list = [{"_id": id} for id in waveform_ids]
        wf_dicts = self.repo.find_many_waveforms(list_of_filters=filter_list)
        wf_entities = [WaveformEntity.from_dict(wf_dict) for wf_dict in
                       wf_dicts]
        return wf_entities

    def get_unique_slew_rates(self, input_df: pd.DataFrame) -> t.List[int]:
        slew_rates = ["ch1_slew", "ch2_slew", "ch3_slew", "ch4_slew"]
        channels = ["ch1_group", "ch2_group", "ch3_group", "ch4_group"]
        cheese = input_df.melt(id_vars=channels, value_vars=slew_rates)
        unique_slewrates = cheese.value.unique()
        return list(unique_slewrates)

    @classmethod
    def convert_to_hyperlink(self, col: pd.Series):
        return col.apply(lambda x: f'=HYPERLINK("/{x}", "image")')

    def make_plot(self, **kwargs) -> plt.Figure:
        raise NotImplementedError

    def set_axes_labels(self, ax: plt.Subplot, xlabel: str = "Time (ms)",
                        ylabel: str = "Voltage (V)") -> None:
        self.set_axes_xlabel(ax=ax, xlabel=xlabel)
        self.set_axes_ylabel(ax=ax, ylabel=ylabel)

    def set_axes_ylabel(self, ax: plt.Subplot,
                        ylabel: str = "Voltage (V)") -> None:
        ax.set_ylabel(ylabel)

    def set_axes_xlabel(self, ax: plt.Subplot,
                        xlabel: str = "Time (ms)") -> None:
        ax.set_xlabel(xlabel)

    def axes_vertical_line(self, ax: plt.Subplot, xloc: int, label: str,
                           ymax: int, ymin: int = 0) -> None:
        COLOR = "black"

        ax.axvline(x=xloc, ymin=ymin, ymax=ymax, c=COLOR)
        ax.text(xloc, 0, label, rotation=90, c=COLOR)

    def axes_set_ylim_from_specs(self, ax, spec_max: float, spec_min: float):
        diff = abs(spec_max - spec_min)
        ten_p = diff * 0.1

        ymax = spec_max + ten_p
        ymin = spec_min - ten_p

        self.axes_set_ylim(ax=ax, ymax=ymax, ymin=ymin)

    def axes_set_ylim(self, ax: plt.Subplot, ymax: float, ymin: float) -> None:
        ax.set_ylim(bottom=ymin, top=ymax)

    def axes_add_max_min(self, ax: plt.Subplot, spec_min: float,
                         spec_max: float, x_end: int, units: str = "",
                         x_start: int = 0) -> None:
        assert spec_max > spec_min, "spec_max must be greater than spec_min: " \
                                    f"{spec_max} >= {spec_min}"
        # CAN USE THESE TERMS TO BETTER SPACE MAX/MIN SPEC TEXT IN THE FUTURE
        # MIN_SPACING = 0.05  # (spec_max-spec_min)/4
        # MAX_SPACING = 0.01
        # ylim = ax.get_ylim()
        COLOR = 'r'
        xlim = ax.get_xlim()

        # spec max
        max_text = f"Spec Max ({spec_max}{units})"
        ax.axhline(y=spec_max, xmax=x_end, xmin=x_start)
        ax.text(xlim[0], spec_max, max_text, c=COLOR)

        # spec min
        min_text = f"Spec Min ({spec_min}{units})"
        ax.axhline(y=spec_min, xmax=x_end, xmin=x_start, c=COLOR)
        ax.text(xlim[0], spec_min, min_text, c=COLOR)

    def axes_add_max(self, ax: plt.Subplot, spec_max: float, x_end: int,
                     x_start: int = 0, text: str = "Spec Max") -> None:
        COLOR = 'r'
        xlim = ax.get_xlim()

        # spec max
        ax.axhline(y=spec_max, xmax=x_end, xmin=x_start)
        ax.text(xlim[0], spec_max, text, c=COLOR)

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

    def save_and_close_plot(self, save_path: Path, fig: plt.Figure):
        assert save_path.suffix == ".png", f"waveform savepath {save_path} " \
                                           f"must be a .png"
        fig.savefig(fname=save_path, format="png")
        plt.close(fig)

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
