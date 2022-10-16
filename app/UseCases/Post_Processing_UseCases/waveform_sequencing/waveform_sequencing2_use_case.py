"""
 **********************************************************************************************************************
# Author: Cruz M. Solano-Nieblas
# Email: csolanon@intel.com
# Date: August 7, 2020
# Version: 2.7
#
# Description: This script tests the order in which a device's traces reach a target (voltage level or percentage of its nominal value) when powered on. It plots the waveform of the traces of interest, as specified by the user, in the same plot to visually analyze the behavior of the traces relative to each other. After the script finishes executing, an excel sheet displaying the results of the trace order test is created.

# How to use: 1) The script is accompanied with the userInput.xlsm Excel file. Open the file and click on the 'Sequencing' tab.
#
#             2) Enter the absolute path to the device's aux_to_main CSV file downloaded from the npoflask2 webpage
#                under 'Path To CSV File'.
#
#             3) For data sets with multiple configurations, enable configurations of interest by entering 'y' in the
#                'Configuration' field. To disable a configuration, enter 'n'. For data sets with one configuration,
#                enable configuration 1 and disable configuration 2.
#
#             For data sets with multiple configurations:
#             Repeat the following steps for each enabled configuration.
#
#             4) Next, input the traces of interest in the order being tested, from top to bottom in the Excel sheet.
#                Note: The order DOES matter, so make sure to input the traces in the order the device is spec'd to
#                      follow (e.g. 12V_MAIN before 3P3V). If you're not sure which traces are valid, input 'test' or
#                      anything in the 'Traces To Be Plotted' field and run the script. You will see the program spit
#                      out an error with a list of valid traces that can be plotted.
#                Another Note: Make sure that the trace names are spelled correctly as this script relies on correct spelling.
#
#             5) Input the corresponding nominal values of the traces as a pure number (e.g 12 instead of 12V).
#
#             6) Input the corresponding target for each trace. The target may be a voltage level or a percentage of its
#                nominal value (90% of 12V).
#                Note: When inputting a percentage, it's CRITICAL that you add the percentage character or else the
#                      program will think it's a voltage level.
#
#             7) Run the script.
#
#             8) When prompted, enter a valid path to where you want the results to be saved.
#
#             9) Let the script do its thing and look for the results when the script finishes executing (:
#
#             P.S. If you receive an error when running the script, these errors most likely concern the userInput.xlsm file.
#                  These errors may be resolved by changing the inputs based off the suggestions from the error messages received.
# **********************************************************************************************************************
"""

import typing as t
import itertools
from collections import defaultdict, OrderedDict, Counter

import pandas as pd
import time

from pandas import ExcelWriter

import gc
import sys
from pathlib import Path
# from shutil import rmtree
# from zipfile import ZipFile


import matplotlib.pyplot as plt
import numpy as np
# import pandas as pd
# import win32com.client as win32
# from openpyxl import load_workbook
# from openpyxl.formatting.rule import Rule
# from openpyxl.styles import PatternFill, Border, Side, Alignment, Font
# from openpyxl.styles.differential import DifferentialStyle
# from openpyxl.utils.cell import _get_column_letter
# from tqdm import tqdm

from app.UseCases.Post_Processing_UseCases.capture_post_processor_use_case import \
    CapturePostProcessingRequestObject, CapturePostProcessorUseCase
from app.shared.Entities import WaveformEntity
from app.UseCases.Post_Processing_UseCases.waveform_sequencing \
    .waveform_sequencing_results import TestpointTimingResult, \
    SequencingCaptureResult
from app.UseCases.Post_Processing_UseCases.capture_timing. \
    capture_timing_use_case import CaptureTimingUseCase

from app.UseCases.Post_Processing_UseCases.waveform_sequencing \
    .waveform_sequencing_results2 import TestpointTimingResult2, \
    SequencingResult

plt.style.use("ggplot")
WAVEFORM_DICT = t.NewType("WAVEFORM_DICT", t.Dict[str, t.List[WaveformEntity]])


class WaveformSequencingRequestObject(CapturePostProcessingRequestObject):
    test_name: str = "Sequencing"
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

    def __init__(self, df: pd.DataFrame, filter_tuple: t.Tuple[str]):
        self.plot_path = self.make_save_path(filter_tuple=filter_tuple,
                                             testname=self.test_name)
        self.df = df
        '''
        self.df = df[[self.DF_WAVEFORM_ID, self.DF_TESTPOINT,
                      self.DF_CAPTURE_T0_INDEX, self.DF_T0_TO_POWERON,
                      self.DF_TOTAL_POWERON_TIME, self.DF_POWERON_INDEX,
                      self.DF_VALID_VOLTAGE, self.DF_TRACE_ORDER,
                      self.DF_POWER_ON_TIME_SPEC, self.DF_TIME_DELTA]]
        '''


class WaveformSequencingUseCase(CapturePostProcessorUseCase):
    sheet_name = "Sequencing"
    EDGE_RAIL_COLUMN_HEADER = "edge_rail"
    TRACE_ORDER_COLUMN_HEADER = "trace_order"
    POWER_ON_TIME_COLUMN_HEADER = "power_on_time_spec"
    TIME_DELTA_COLUMN_HEADER = "time_delta"

    def _test_specific_columns(self):
        return [self.EDGE_RAIL_COLUMN_HEADER, self.TRACE_ORDER_COLUMN_HEADER,
                self.POWER_ON_TIME_COLUMN_HEADER,
                self.TIME_DELTA_COLUMN_HEADER,
                CaptureTimingUseCase.POWERON_INDEX,
                CaptureTimingUseCase.CAPTURE_T0_INDEX,
                CaptureTimingUseCase.CAPTURE_RAMP_T0,
                CaptureTimingUseCase.RAIL_POWERON_FROM_T0,
                CaptureTimingUseCase.TOTAL_POWERON_TIME]

    def post_process(self, request_object: WaveformSequencingRequestObject) -> \
            pd.DataFrame:
        """
        The Sequencing Test validates the waveform_names ramp in the correct order
        and within the given time limit.
            - Validate waveform sequence
            - Validate waveform ramp timing

        @param request_object:
        @return:
        """
        # Filter raw dataframe

        filtered_df = self.filter_df(raw_df=request_object.df)

        # by = list(request_object.groupby_list)
        # by_without_testpoint = by[:-1]
        # if not len(by):
        #    raise AttributeError("groupby list must be provided for "
        #                         "WaveformSequencing!")

        '''

        timing_results = list()
        for testpoint, testpoint_df in request_object.df.groupby(
                by="testpoint"):
            timing_result = TestpointTimingResult2(df=testpoint_df)
            random_result = timing_result.passfail()
            timing_results.append(timing_result)

            print(random_result)
        '''

        sequence_result = SequencingResult(df=filtered_df)
        sequencing_dict = sequence_result.passfail()

        # sample_groups = filtered_df.groupby(by=by)
        # for filt, group_df in sample_groups:
        overlay_plot = self.plot_sequencing_overlay(df=filtered_df,
                                                    save_path=request_object.plot_path)
        sequencing_dict["Overlay Plot"] = self.convert_to_hyperlink(
            col=pd.Series([overlay_plot]))

        distinct_plot = self.plot_sequencing_distinct(df=filtered_df,
                                                      save_path=request_object.plot_path)
        sequencing_dict["Distinct Plot"] = self.convert_to_hyperlink(
            col=pd.Series([distinct_plot]))

        result_df = pd.DataFrame(sequencing_dict, columns=list(
            sequencing_dict.keys()), index=[0])

        return result_df
        # return result_df

    def plot_sequencing_overlay(self, df: pd.DataFrame,
                                save_path: Path) -> Path:
        path = save_path.with_name(
            f"Overlay_{save_path.name}").with_suffix(".png")
        plot_title = "Overlay Slew Rate Sequencing"

        fig = self.plot_waveforms_by_slewrate(df=df, fig_title=plot_title)

        self.save_and_close_plot(save_path=path, fig=fig)
        assert path.exists(), "Sequencing graph should have been " \
                              f"saved, but doesn't exist? {path}"

        return path

    def plot_sequencing_distinct(self, df: pd.DataFrame,
                                 save_path: Path) -> Path:
        path = save_path.with_name(
            f"Distinct_{save_path.name}").with_suffix(".png")
        plot_title = "Distinct Slew Rate Sequencing"

        fig = self.plot_waveforms_by_testpoint(df=df, fig_title=plot_title)

        self.save_and_close_plot(save_path=path, fig=fig)
        assert path.exists(), "Sequencing graph should have been " \
                              f"saved, but doesn't exist? {path}"

        return path

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

    def _plot_waveform_by_slewrate(self, ax: plt.axis, waveforms: t.List[
        WaveformEntity], t0_list: t.List[float]):

        for wf in waveforms:
            ax.plot(wf.x_axis_in_milliseconds(), wf.y_axis())

        ymin, ymax = ax.get_ylim()

        self._plot_t0_list(ax=ax, t0_list=t0_list,
                           t0_voltage=ymax // 2)

    def _extract_t0(self, df: pd.DataFrame):
        t0_capture_column = "capture_t0"

        t0_values = df[t0_capture_column].values
        return t0_values

    def _set_waveform_colors(self, df: pd.DataFrame) -> t.Dict[str, str]:
        color_dict = {}
        waveform_df = df.set_index("testpoint").sort_values(by="trace_order")
        for wf_name, color in zip(waveform_df.index.unique(),
                                  self.color_list()):
            color_dict[wf_name] = color

        return color_dict

    def _shift_x_axis_to_t0(self, waveform: WaveformEntity, t0: float,
                            start_time: int = -10) -> \
            t.Tuple[np.array, np.array]:

        x = waveform.x_axis_in_milliseconds() - t0
        shift_idx = len(np.where(x >= start_time)[0])

        shifted_y = waveform.y_axis()[-shift_idx:]
        shifted_x = x[-shift_idx:]

        return shifted_x, shifted_y

    def _plot_sequencing_by_slewrate(self, ax: plt.axes, df: pd.DataFrame,
                                     color_list: dict, ax_title: str):
        plot_start_time = -10
        # Load waveforms from dataframe to plot
        df.drop_duplicates(inplace=True)
        wfs = self.load_waveforms_by_df(df=df)
        waveform_df = df.set_index("waveform_id")
        legend = defaultdict(str)

        # Plot Waveforms
        for wf in wfs:
            wf_row = waveform_df.loc[wf._id]
            wf_color = color_list[wf_row.testpoint]
            shifted_x, shifted_y = \
                self._shift_x_axis_to_t0(waveform=wf, t0=wf_row['capture_t0'],
                                         start_time=plot_start_time)
            line = ax.plot(shifted_x, shifted_y, c=wf_color,
                           alpha=0.8)
            if wf.testpoint not in legend:
                legend[wf.testpoint] = line

        ax.set_title(ax_title)

        # Plot t0
        ymin, ymax = ax.get_ylim()
        t0_voltage = ymax // 2
        self._plot_t0_list(ax=ax, t0_list=[0], t0_voltage=t0_voltage)

        # Add Legend
        lines = [line[0] for line in legend.values()]
        names = [name for name in legend.keys()]
        ax.legend(tuple(lines), tuple(names),
                  loc='upper left')
        # Change Checkmarks
        # locs, labels = ax.set_xticks(np.linspace(shifted_x[0], shifted_x[-1],
        #                                         num=100))
        # locs, labels = ax.set_xticks()

    def plot_waveforms_by_testpoint(self, df: pd.DataFrame, fig_title: str) \
            -> plt.Figure:
        sequence_ordered_df = df.sort_values(by="trace_order")
        testpoints = sequence_ordered_df["testpoint"].unique()

        waveform_colors = self._set_waveform_colors(df=df)

        num_graphs = len(testpoints)
        fig, axs = plt.subplots(nrows=num_graphs, ncols=1, figsize=(20, 20),
                                sharex=True)
        fig.suptitle(f"{fig_title}")

        for testpoint, ax in zip(testpoints, axs):
            testpoint_df = sequence_ordered_df[
                sequence_ordered_df["testpoint"] == testpoint]
            color = waveform_colors[testpoint]

            self._plot_sequencing_by_testpoint(ax=ax, df=testpoint_df,
                                               color=color,
                                               ax_title=f"{testpoint}")

        fig.tight_layout()

        return fig

    def _plot_sequencing_by_testpoint(self, ax: plt.axes, df: pd.DataFrame,
                                      color: str, ax_title: str):
        plot_start_time = -10
        # Load waveforms from dataframe to plot
        wfs = self.load_waveforms_by_df(df=df)
        waveform_df = df.set_index("waveform_id")

        # Plot Waveforms
        for wf in wfs:
            wf_row = waveform_df.loc[wf._id]
            shifted_x, shifted_y = \
                self._shift_x_axis_to_t0(waveform=wf, t0=wf_row['capture_t0'],
                                         start_time=plot_start_time)
            line = ax.plot(shifted_x, shifted_y, c=color,
                           alpha=0.8)

        ax.set_title(ax_title)

        # Plot t0
        ymin, ymax = ax.get_ylim()
        t0_voltage = ymax // 2
        self._plot_t0_list(ax=ax, t0_list=[0], t0_voltage=t0_voltage)

        # Add Legend
        ax.legend(line, wf.testpoint,
                  loc='upper left')

    def plot_waveforms_by_slewrate(self, df: pd.DataFrame, fig_title: str) -> \
            plt.Figure:
        slew_rates = self.get_unique_slew_rates(input_df=df)

        waveform_colors = self._set_waveform_colors(df=df)

        num_graphs = len(slew_rates)

        fig, axs = plt.subplots(nrows=num_graphs, ncols=1, figsize=(20, 20),
                                sharex=True)
        fig.suptitle(f"{fig_title}")

        if num_graphs == 1:
            slew_rate = slew_rates[0]
            self._plot_sequencing_by_slewrate(ax=axs, df=df,
                                              color_list=waveform_colors,
                                              ax_title=f"Slew Rate: "
                                                       f"{slew_rate}V/s")
        else:
            for slew_rate, ax in zip(slew_rates, axs):
                slew_df = self.filter_df_by_slewrate(filtered_df=df,
                                                     slew_rate=slew_rate)
                self._plot_sequencing_by_slewrate(ax=ax, df=slew_df,
                                                  color_list=waveform_colors,
                                                  ax_title=f"Slew Rate: {slew_rate}V/s")

        fig.tight_layout()

        # self.save_plot(result_dict={}, fig=fig, filename=)
        return fig

    def business_logic(self, **kwargs) -> OrderedDict:
        return OrderedDict()

    def create_timing_results(self, filtered_df: pd.DataFrame,
                              wf_dict: WAVEFORM_DICT, capture_number: int
                              ) -> SequencingCaptureResult:
        """
        @param filtered_df:
        @param wf_dict:
        @return:
        """
        group_result = SequencingCaptureResult(capture_number=capture_number)

        traceOrder = self.get_trace_order(df=filtered_df)

        previous_result = None
        for testpoint in traceOrder:
            testpoint_wfs = wf_dict[testpoint]
            edge, order, power_on_spec, previous_delta = \
                self.get_testpoint_specs(testpoint=testpoint, df=filtered_df)

            previous_result = self.create_sequencing_testpoint_result(
                previous_result=previous_result,
                min_delta=previous_delta,
                spec_max=power_on_spec,
                testpoint_wfs=testpoint_wfs)
            group_result.results.append(previous_result)

        return group_result

    def _spec_target(self, testpoint: str, filtered_df: pd.DataFrame) -> float:
        spec_target = filtered_df[filtered_df["testpoint"] == testpoint][
            self.POWER_ON_TIME_COLUMN_HEADER]
        r = float(spec_target.values[0])
        return r

    def create_sequencing_testpoint_result(self, testpoint_wfs: t.List[
        WaveformEntity], previous_result: TestpointTimingResult = None,
                                           min_delta: float = 0,
                                           spec_max: float = 0) -> TestpointTimingResult:
        """
        @param testpoint_wfs:  list of a testpoints waveform_names
        @param previous_result: The testpoint in order -1 position
        @param min_delta: allows variance from previous rail (used for when
        many rails power-on at the same time).
        @param spec_max: maximum power-on time
        @return:
        """
        min_index, max_index, min_t, max_t = self._testpoint_ramp_timing(
            wf_list=testpoint_wfs)
        if previous_result is None:
            result = TestpointTimingResult(
                testpoint=testpoint_wfs[0].testpoint, order=0, spec_min=0,
                spec_max=np.inf, max_time=max_t, min_time=min_t, t0=min_t,
                waveform_id=testpoint_wfs[0]._id)
        else:
            order = previous_result.order + 1
            spec_min = previous_result.min_time - min_delta
            result = TestpointTimingResult(
                testpoint=testpoint_wfs[0].testpoint, order=order,
                spec_min=spec_min, spec_max=spec_max, max_time=max_t,
                min_time=min_t, t0=previous_result.t0,
                waveform_id=testpoint_wfs[0]._id)
        return result

    def find_t0(self, traceOrder: t.List[str],
                wf_dict: WAVEFORM_DICT) -> t.Tuple[int, int, float, float]:
        wf_0 = wf_dict[traceOrder[0]]
        return self._testpoint_ramp_timing(wf_list=wf_0)

    def _testpoint_ramp_timing(self, wf_list: t.List[WaveformEntity]) -> \
            t.Tuple[int, int, float, float]:
        """

        @param wf_list:
        @return:
        """
        min_index = np.inf
        max_index = 0
        min_t = np.inf
        max_t = 0
        for wf in wf_list:
            if wf.units == "A":
                continue
            index = wf.steady_state_index()
            min_index = min(min_index, index)
            max_index = max(max_index, index)
            if min_index == index:
                min_t = wf.x_axis_in_milliseconds()[index]
            if max_index == index:
                max_t = wf.x_axis_in_milliseconds()[index]
        return min_index, max_index, round(min_t, 2), round(max_t, 2)

    def validate_testpoint_poweron_time(self, t0: float, target_time: float,
                                        wfs: t.List[WaveformEntity]) -> t.Dict:
        """

        @param t0:
        @param target_time:
        @param wfs:
        @return:
        """

        min_index, max_index, min_t, max_t = self._testpoint_ramp_timing(
            wf_list=wfs)

        adj_min = min_t - t0
        adj_max = max_t - t0

        wf_name = wfs[0].testpoint

        if adj_min >= 0 and target_time >= adj_max:
            if adj_max == adj_min:
                result = {"Result": "Pass",
                          "Reason": f"{wf_name} ramped in {adj_min}ms, which "
                                    f"is prior to {target_time}ms"}
            else:
                result = {"Result": "Pass",
                          "Reason": f"{wf_name} ramped between "
                                    f"{adj_min} to {adj_max}ms, which is prior "
                                    f"to {target_time}ms"}

        elif adj_min < 0:
            result = {"Result": "Fail",
                      "Reason": f"{wf_name} ramped prior to first rail"}
        elif target_time <= adj_max:
            result = {"Result": "Fail",
                      "Reason": f"{wf_name} ramped at {adj_max}ms, "
                                f"after target time of {target_time}ms"}
        else:
            result = {"Result": "Fail",
                      "Reason": "A case occured that wasn't expected."}

        result["min"] = adj_min
        result["max"] = adj_max
        return result

    def post_process_only_plots(self,
                                request_object: WaveformSequencingRequestObject) -> \
            pd.DataFrame:
        """
        The Sequencing Test validates the waveform_names ramp in the correct order
        and within the given time limit.
            - Validate waveform sequence
            - Validate waveform ramp timing
    
        @param request_object:
        @return:
        """
        # Filter raw dataframe

        filtered_df = self.filter_df(raw_df=request_object.df)

        by = request_object.groupby_list
        if len(by):
            by = ["runid", "capture"]

        sample_groups = filtered_df.groupby(by=by)
        for filt, group_df in sample_groups:
            for slew_rate in [200, 1000, 5000, 26400]:
                runids = [int(runid) for runid in group_df.runid.unique()]
                captures = self.repo.query_waveform_captures(filters=
                {
                    "runid": {"$in": runids},
                    # "environment.chamber_setpoint": 60,
                    "environment.power_supply_channels": {"$elemMatch": {
                        "slew_rate": slew_rate,
                        "channel_on": True}}
                }, projection={"capture": 1, "_id": 0})
                test_captures = []
                for capture in captures:
                    test_captures.append(capture["capture"])

                wfs = self.repo.query_waveforms(filters={
                    "runid": {"$in": runids},
                    "capture": {"$in": test_captures}
                })
                wf_entities = [WaveformEntity.from_dict(adict=wf) for wf in wfs]

                trace_order = self.get_trace_order(df=group_df)

                fig = self.makePlot(traceOrder=trace_order,
                                    wf_entities=wf_entities)
                wf_count = len(wf_entities)
                path = r"C:\Users\ammonk\OneDrive - Intel Corporation\Desktop\Test_Folder\fake_uploads\fake_results"
                project = group_df.dut.unique()[0]
                serial = group_df.serial_number.unique()[0]

                fig_title = f"{project} Sample {serial} With {slew_rate} V/s " \
                            f"[{wf_count} Waveforms!]"
                self._title_plot(fig=fig, title=fig_title)

                fig_name = f"{project}_{serial}_{slew_rate}"
                self._save_figure(fig=fig, path=path, fig_name=fig_name)

        return 0

    def get_trace_order(self, df: pd.DataFrame) -> t.List[str]:
        traceOrder_df = df[["testpoint", "trace_order"]]
        traceOrder_df.sort_values(by="trace_order", inplace=True)
        traceOrder = traceOrder_df.testpoint.unique()

        return list(traceOrder)

    def get_testpoint_specs(self, testpoint: str, df: pd.DataFrame) -> \
            t.Tuple[bool, int, float, float]:
        testpoint_df = df[df.testpoint == testpoint]
        edge_rail, order, power_on_spec, previous_delta = \
            testpoint_df[self._test_specific_columns()].iloc[0].values
        return edge_rail, order, power_on_spec, previous_delta

    def flip(self, items, ncol):
        return itertools.chain(*[items[i::ncol] for i in range(ncol)])

    def makePlot(self, traceOrder: t.List[str], wf_entities: t.List[
        WaveformEntity]) -> plt.Figure:
        line_dict = defaultdict(list)

        fig = plt.figure(figsize=(10, 10), constrained_layout=True)
        gs = fig.add_gridspec(ncols=1, nrows=3)
        plot_ax = fig.add_subplot(gs[1:, 0])
        colors = self.color_list()

        for wf in wf_entities:
            color_index = traceOrder.index(wf.testpoint)
            color = colors[color_index]
            line = plot_ax.plot(wf.x_axis_in_milliseconds(), wf.y_axis(),
                                c=color,
                                alpha=1, zorder=8, label=wf.testpoint)
            line_dict[wf.testpoint].extend(line)

        handles = []
        for trace in traceOrder:
            handles.append(line_dict[trace][0])

        fhandles = self.flip(handles, len(traceOrder))
        flabels = self.flip(
            [f"{i}. {name}" for i, name in enumerate(traceOrder)],
            len(traceOrder))

        num_columns = len(traceOrder) // 4

        plot_ax.legend(fhandles, flabels,
                       loc="upper center", ncol=num_columns,
                       bbox_to_anchor=(0.5, 1.5), fontsize='small')
        plot_ax.set_xlabel("Time (s)")
        plot_ax.set_xlim(auto=True)
        plot_ax.set_ylabel("Voltage (V)")
        plot_ax.set_ylim(auto=True)

        return fig

    @classmethod
    def color_list(cls) -> t.List[str]:
        return ["tab:blue", "tab:orange", "tab:green", "tab:red",
                "tab:purple", "tab:brown", "tab:pink", "tab:gray",
                "tab:olive", "tab:cyan", "red", "yellow", "blue", "orange",
                "green", "purple", "crimson", "gold", "dodgerblue",
                "darkorange", "lime", "deeppink", "firebrick", "olive", "navy",
                "peru", "seagreen", "indigo", "tomato", "goldenrod",
                "royalblue", "chocolate", "springgreen", "violet", "maroon",
                "lemonchiffon"]

    def _title_plot(self, fig: plt.Figure, title: str) -> None:
        fig.suptitle(title)

    def _save_figure(self, fig, path, fig_name):
        path_obj = Path(path)
        save_path = path_obj.joinpath(fig_name).with_suffix(".png")
        fig.savefig(save_path, format='png', dpi=200)

        plt.clf()
        gc.collect()


