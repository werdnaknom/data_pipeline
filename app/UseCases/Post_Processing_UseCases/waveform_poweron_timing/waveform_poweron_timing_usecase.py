import typing as t
from collections import defaultdict, OrderedDict, Counter
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from app.UseCases.Post_Processing_UseCases.testpoint_post_processor_use_case \
    import TestpointPostProcessingRequestObject, TestPointPostProcessorUseCase

from app.UseCases.Post_Processing_UseCases.waveform_poweron_timing \
    .waveform_poweron_timing_results import TestpointTimingResult

from app.UseCases.Post_Processing_UseCases.capture_post_processor_use_case \
    import CapturePostProcessorUseCase, CapturePostProcessingRequestObject

from app.UseCases.Post_Processing_UseCases.waveform_min_max_processing \
    .min_max_results import TestPointMinMaxResult

from app.UseCases.Post_Processing_UseCases.capture_timing. \
    capture_timing_use_case import CaptureTimingUseCase

from app.shared.Entities import WaveformEntity

plt.style.use("ggplot")


class PowerOnTimingRequestObject(CapturePostProcessingRequestObject):
    test_name: str = "Power-onTime"

    plot_path: Path

    def __init__(self, df: pd.DataFrame, filter_tuple: t.Tuple[str]):
        self.df = df
        self.plot_path = self.make_save_path(filter_tuple=filter_tuple,
                                             testname=self.test_name)


class PowerOnTimingUseCase(CapturePostProcessorUseCase):
    test_name: str = "Power-on Time"
    DF_WAVEFORM_ID: str = "waveform_id"
    DF_TESTPOINT: str = "testpoint"
    DF_CAPTURE_T0_INDEX: str = "capture_t0_index"
    DF_T0_TO_POWERON: str = "t0_to_poweron"
    DF_TOTAL_POWERON_TIME: str = "total_poweron_time"
    DF_POWERON_INDEX: str = "poweron_index"
    DF_VALID_VOLTAGE: str = "valid_voltage"
    DF_TRACE_ORDER: str = "trace_order"
    DF_POWER_ON_TIME_SPEC: str = "power_on_time_spec"
    DF_TIME_DELTA: str = "time_delta"

    def _test_specific_columns(self):
        return [CaptureTimingUseCase.POWERON_INDEX,
                CaptureTimingUseCase.CAPTURE_T0_INDEX,
                CaptureTimingUseCase.RAIL_POWERON_FROM_T0,
                CaptureTimingUseCase.TOTAL_POWERON_TIME]

    def post_process(self,
                     request_object: PowerOnTimingRequestObject) -> pd.DataFrame:
        filtered_df = self.filter_df(raw_df=request_object.df)

        result_df = pd.DataFrame()

        slew_rates = self.get_unique_slew_rates(input_df=filtered_df)

        for testpoint, testpoint_df in request_object.df.groupby(
                by=self.DF_TESTPOINT):
            testpoint_timing = TestpointTimingResult(df=testpoint_df)
            timing_result = testpoint_timing.passfail()
            timing_result['TestPoint'] = testpoint
            timing_plot = self.plot_poweron_timing(
                df=testpoint_df,
                save_path=request_object.plot_path,
                testpoint=testpoint)
            timing_result["Timing Plot"] = self.convert_to_hyperlink(
                pd.Series([timing_plot]))

            timing_histogram = self.plot_poweron_histogram(df=testpoint_df,
                                                           save_path=request_object.plot_path,
                                                           testpoint=testpoint)
            timing_result["Timing Histogram"] = self.convert_to_hyperlink(
                pd.Series([timing_histogram]))

            timing_result_df = pd.DataFrame(timing_result, columns=list(
                timing_result.keys()), index=[0])

            result_df = pd.concat([result_df, timing_result_df])

        return result_df

    def plot_poweron_timing(self, df: pd.DataFrame, save_path: Path,
                            testpoint: str) -> Path:
        path = save_path.with_name(f"power_on_{testpoint}_timing").with_suffix(
            ".png")

        plot_title = f"{testpoint} Power-on Timing"

        fig = self.plot_testpoint_timing(df=df, fig_title=plot_title)

        self.save_and_close_plot(save_path=path, fig=fig)
        assert path.exists(), "Sequencing graph should have been " \
                              f"saved, but doesn't exist? {path}"

        return path

    def plot_poweron_histogram(self, df: pd.DataFrame, save_path: Path,
                               testpoint: str) -> Path:

        path = save_path.with_name(f"power_on_"
                                   f"{testpoint}_histogram").with_suffix(".png")
        plot_title = f"{testpoint} Power-on Timing"

        fig = self.plot_testpoint_histogram(df=df, fig_title=plot_title)
        self.save_and_close_plot(save_path=path, fig=fig)
        assert path.exists(), "Timing Histogram should have been " \
                              f"saved, but doesn't exist? {path}"

        return path

    def plot_testpoint_histogram(self, df: pd.DataFrame, fig_title: str) -> \
            plt.Figure:
        print(df.shape)

        fig, axs = plt.subplots(nrows=2, ncols=1, figsize=(10, 10))
        fig.suptitle(fig_title)

        df.rename(columns={self.DF_T0_TO_POWERON: "Power-on Time (ms)",
                           "meta_json_temperature_setpoint": "Temperature (C)",
                           "meta_json_power_supply_slew_1": "Slew Rate ("
                                                            "V/s)"},
                  inplace=True)

        # axs.histogram(timings, bins=5)
        sns.color_palette("tab10")
        try:
            sns.histplot(data=df, x="Power-on Time (ms)", kde=True,
                         ax=axs[0], discrete=True,  # multiple="stack",
                         hue="Temperature (C)", palette="tab10")
            sns.histplot(data=df, x="Power-on Time (ms)", kde=True,
                         ax=axs[1], discrete=True,  # multiple="stack",
                         hue="Slew Rate (V/s)", palette="tab10")
        except:
            print(fig_title)

        return fig

    def plot_testpoint_timing(self, df: pd.DataFrame,
                              fig_title: str) -> plt.Figure:
        PLOT_START_TIME = -10

        fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(10, 10))
        fig.suptitle(fig_title)

        wfs = self.load_waveforms_by_df(df=df)
        waveform_df = df.set_index("waveform_id")
        legend = defaultdict(str)

        valid_voltage = waveform_df["valid_voltage"].unique()[0]

        # Plot Testpoint Waveforms
        for wf in wfs:
            wf_row = waveform_df.loc[wf._id]
            wf_color = 'b'
            shifted_x, shifted_y = \
                self._shift_x_axis_to_t0(waveform=wf, t0=wf_row['capture_t0'],
                                         start_time=PLOT_START_TIME)
            line = axs.plot(shifted_x, shifted_y, c=wf_color,
                            alpha=0.8)
            axs.legend(loc='upper left')

        # t0_list =
        ymin, ymax = axs.get_ylim()
        t0_voltage = ymax // 2

        self._plot_expected_voltage(ax=axs, voltage_level=valid_voltage,
                                    voltage_text=f"Valid Voltage ({valid_voltage})")
        self._plot_ground_level(ax=axs)

        self._plot_t0_list(ax=axs, t0_list=[0], t0_voltage=t0_voltage)
        self._plot_t0_list(ax=axs, t0_list=waveform_df[self.DF_T0_TO_POWERON],
                           t0_voltage=t0_voltage)

        fig.tight_layout()

        return fig

    def _shift_x_axis_to_t0(self, waveform: WaveformEntity, t0: float,
                            start_time: int = -10) -> \
            t.Tuple[np.array, np.array]:

        x = waveform.x_axis_in_milliseconds() - t0
        shift_idx = len(np.where(x >= start_time)[0])

        shifted_y = waveform.y_axis()[-shift_idx:]
        shifted_x = x[-shift_idx:]

        return shifted_x, shifted_y

    def _plot_expected_voltage(self, ax: plt.axis, voltage_level: float,
                               color: str = "r", voltage_text: str = ""):
        ax.axhline(y=voltage_level, c=color)
        if voltage_text:
            self._add_text(ax=ax, y=voltage_level + 0.1,
                           text=voltage_text, x=0, color=color)

    def _add_text(self, ax: plt.Axes, text: str, x: float, y: float,
                  color: str = "r", fontsize: int = 12):
        ax.text(x=x, y=y, s=text, c=color, fontsize=fontsize)

    def _plot_ground_level(self, ax: plt.axis):
        self._plot_expected_voltage(ax=ax, voltage_level=0, color='k')

    def _plot_t0_list(self, ax: plt.axis, t0_list: t.List[float],
                      t0_voltage: float):
        round_t0 = np.round(t0_list, 1)
        most_common = Counter(round_t0).most_common(1)[0][0]
        t0_max = np.max(round_t0)
        t0_min = np.min(round_t0)

        # Plot most common
        ax.axvline(x=most_common, c='black')
        ax.text(x=most_common - 0.1, y=t0_voltage, s="t0", rotation=-90)

        # Plot t0_max
        if t0_max != most_common:
            ax.axvline(x=t0_max, c='black', linestyle="--")

        if t0_min != most_common:
            ax.axvline(x=t0_min, c='black', linestyle="--")
