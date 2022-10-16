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
from collections import defaultdict, OrderedDict

import pandas as pd

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

from app.UseCases.Post_Processing_UseCases.post_processing_use_case import \
    PostProcessingUseCase, PostProcessingRequestObject
from app.shared.Entities import WaveformEntity
from app.UseCases.Post_Processing_UseCases.waveform_sequencing \
    .waveform_sequencing_results import TestpointTimingResult, \
    SequencingCaptureResult

plt.style.use("ggplot")
WAVEFORM_DICT = t.NewType("WAVEFORM_DICT", t.Dict[str, t.List[WaveformEntity]])


class WaveformSequencingUseCase(PostProcessingUseCase):
    sheet_name = "Sequencing"
    EDGE_RAIL_COLUMN_HEADER = "edge_rail"
    TRACE_ORDER_COLUMN_HEADER = "trace_order"
    POWER_ON_TIME_COLUMN_HEADER = "power_on_time_spec"
    TIME_DELTA_COLUMN_HEADER = "time_delta"

    def _test_specific_columns(self):
        return [self.EDGE_RAIL_COLUMN_HEADER, self.TRACE_ORDER_COLUMN_HEADER,
                self.POWER_ON_TIME_COLUMN_HEADER, self.TIME_DELTA_COLUMN_HEADER]




    def post_process(self, request_object: PostProcessingRequestObject) -> \
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
        if not len(by):
            raise AttributeError("groupby list must be provided for "
                                 "WaveformSequencing!")

        sample_groups = filtered_df.groupby(by=by)


        result_df = pd.DataFrame()
        for filt, group_df in sample_groups:
            for slew_rate in self.get_main_slew_rates(filtered_df=group_df):
                slew_df = self.filter_df_by_slewrate(filtered_df=group_df,
                                                     slew_rate=slew_rate,
                                                     group="Main")
                ''' For sequencing, each capture needs to be analyzed 
                individually.  The waveform timing is built from the first rail 
                up on each capture. '''
                temperatures = self.get_unique_temperatures(
                    filtered_df=slew_df)
                main_voltages = self.get_main_voltages(filtered_df=slew_df)
                aux_voltages = self.get_aux_voltages(filtered_df=slew_df)

                for capture in slew_df.capture.unique():
                    capture_df = slew_df[slew_df.capture == capture]
                    wf_dict: WAVEFORM_DICT = self.load_waveforms_dict(
                        df=capture_df)

                    capture_sequence_result = self.create_timing_results(
                        filtered_df=capture_df, wf_dict=wf_dict,
                        capture_number=capture)

                    result_dict = capture_sequence_result.passfail()
                    capture_result_df = pd.DataFrame(result_dict,
                                                     index=[capture],
                                                     columns=list(
                                                         result_dict.keys()))

                    sequencing_result = pd.DataFrame()
                    timing_result = pd.DataFrame()
                    for index, row in capture_result_df.iterrows():
                        ''' 
                        The capture_results can build the
                         CAPTURE SEQUENCING RESULT and 
                         WAVEFORM TIMING results
                        '''
                        #CAPTURE SEQUENCING RESULT


                    traceOrder = self.get_trace_order(df=capture_df)
                    wf_list = [wf_dict[wf_name][0] for wf_name in traceOrder]
                    plot = self.makePlot(traceOrder=traceOrder,
                                         wf_entities=wf_list)


                    result_df = pd.concat([result_df, capture_result_df],
                                          ignore_index=True)

                # results_df = pd.concat([passfail_result.to_result(),
                #                        results_df], ignore_index=True)

        return result_df


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

    def post_process_only_plots(self, request_object:
    PostProcessingRequestObject) -> \
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
        return [
            "red", "yellow", "blue", "orange", "green", "purple",
            "crimson", "gold", "dodgerblue", "darkorange", "lime", "deeppink",
            "firebrick", "olive", "navy", "peru", "seagreen", "indigo",
            "tomato", "goldenrod", "royalblue", "chocolate", "springgreen",
            "violet",
            "maroon", "lemonchiffon"]

    def _title_plot(self, fig: plt.Figure, title: str) -> None:
        fig.suptitle(title)

    def _save_figure(self, fig, path, fig_name):
        path_obj = Path(path)
        save_path = path_obj.joinpath(fig_name).with_suffix(".png")
        fig.savefig(save_path, format='png', dpi=200)

        plt.clf()
        gc.collect()

    '''
    
    def read_userInput(userInput, dataCSV, configs):
        """
        Reads and validates all userInput
        :param userInput: pandas DataFrame of user input to be validated
        :param dataCSV: path to the dataCSV file
        :param configs: dictionary containing the test configurations
        :return: pandas DataFrame of data in CSV file, trace names, corresponding nominal     values, corresponding targets, number of channels for first configuration allowed
        """
    
        # read dataCSV file
        assert Path(
            dataCSV).is_file(), f"{dataCSV.resolve()} is not a valid path to an existing     dataCSV file. Make sure the " \
                                "path to the dataCSV file is specified correctly."
        df = pd.read_csv(dataCSV)
    
        # process the rest of the userInput
        raw_testpoints = list()  # list that will contain testpoint names
        if df['testrun_json_configuration'].nunique() > 1 or df[
            'testrun_json_configuration'].isnull().any():  # if there are multiple     configurations in the same dataCSV file
            temp = df['testrun_json_configuration']  # filter configuration column
            count = 0
            for confignum, enabled in configs.items():
                i = temp[temp == int(confignum)].index[
                    0]  # find where the config begins in the df
                fltr = temp == int(confignum)  # build a filter out of the confignum
                channelNums = df['testpoint'][
                    fltr].nunique()  # number of channels that were used in the configuration
                if enabled == 'y':
                    testpoints = list(df.loc[i:i + channelNums - 1, 'testpoint'])
                    raw_testpoints.extend(testpoints)
                    if count == 0:
                        chan = channelNums
                    count += 1
                else:
                    df = df[~fltr]
    
            df.reset_index(drop=True, inplace=True)
        else:
            chan = df['scope_channel'][-1]
            raw_testpoints = list(df.loc[0:(chan - 1),
                                  'testpoint'])  # testpoint names in the dataCSV file
    
        temp = userInput['traces'].apply(str.upper).to_list()
        testpoints = read_traces(temp, raw_testpoints)
    
        temp = userInput['nominalVals'].to_list()
        nominalVals = read_nominalVals(temp)
    
        temp = userInput['targets'].to_list()
        targets = read_targets(temp, nominalVals)
    
        return df, testpoints, nominalVals, targets, chan
    
    
    
    
    
    
    
    
    
    
    
    def makePlot(namelist, targetVals, delta, legendCols):  # outer function
        """
        Generates and configures an empty plot.
        :param namelist: list of trace names to be plotted
        :param targetVals: list of corresponding target values
        :param delta: time between samples
        :param legendCols: number of columns for the legend
        :return: pointer to drawOnPlot function
        """
    
        # axes generation and configuration
        ax = plt.axes(facecolor='#D3D3D3', zorder=1)
        plt.grid(color='w', linestyle='solid', zorder=1, linewidth=0.5)
        ax.set_xlabel("Time (s)")
        ax.set_xlim(auto=True)
        ax.set_ylabel("Voltage (V)")
        ax.set_ylim(auto=True)
        colorlist = plt.rcParams['axes.prop_cycle'].by_key()['color']
        targetLocs = list()  # empty list to contain all the target locations
        order = list(
            range(len(namelist)))  # empty list to maintain the order of all traces
        i = 0
    
        def drawOnPlot(tracename, timestamps, data, loc, traceIndex,
                       allTracesAdded):  # inner function
            """
            Plots the data values that correspond to the timestamps on the current axes.
            Also plots vertical and horizontal dashed lines that locate the target value.
            :param tracename: name of the trace to be plotted
            :param timestamps: 1-D numPy array that contains the timestamp values
            :param data: 1-D numPy array that contains the data values to be plotted
            :param loc: location where the trace reached its target
            :param traceIndex: index of the trace in the order specified by the user
            :param allTracesAdded: flag to determine when all traces have been added
            :return: status of sequencing test
            """
            nonlocal i
            plt.plot(timestamps, data, axes=ax, alpha=1, zorder=8, label=tracename,
                     color=colorlist[traceIndex])  # plot data vs timestamps
            targetLocs.insert(traceIndex,
                              loc)  # add location in the order specified by the user
            order[
                traceIndex] = i  # this list indicates the order of each trace plotted
            i += 1
    
            if ~np.isnan(loc):  # if the trace reaches its target
                # plot the location where the trace reaches its target
                plt.axvline(timestamps[loc], linestyle='--', linewidth=0.8,
                            color=colorlist[traceIndex], alpha=0.63,
                            zorder=2)
                plt.axhline(data[loc], linestyle='--', linewidth=0.8,
                            color=colorlist[traceIndex], alpha=0.63, zorder=2)
            if allTracesAdded:
                handles, labels = ax.get_legend_handles_labels()
                handles[:] = [handles[x] for x in order]
                labels[:] = [labels[x] for x in
                             order]  # this is to manually order the legend so the names appear     in the order specified by the user
                l = plt.legend(handles, labels, loc='upper center',
                               bbox_to_anchor=(0.5, 1.1), ncol=legendCols,
                               fontsize='x-small', fancybox=True, shadow=True,
                               prop={'size': 7})  # add a legend to the plot
                status, failList, seqTime = passfail(targetLocs, namelist,
                                                     delta)  # perform the sequencing test
                if status.find('FAIL') > -1:  # if it failed the sequencing test
                    texts = l.get_texts()
                    if status.find('did not reach their target',
                                   20) > -1:  # if it didn't reach its target
                        for fail in failList:
                            idx = namelist.index(
                                fail)  # this is the index of the trace that failed
                            plt.axhline(targetVals[idx], linewidth=0.8,
                                        color=colorlist[idx], alpha=0.63,
                                        zorder=2)  # plot where the target was
                            texts[idx].set_color(
                                "red")  # highlight in the legend which trace failed
                    else:  # if the traces are out of order
                        for fail in failList:
                            idx = namelist.index(fail)
                            texts[idx].set_color(
                                "red")  # highlight in the legend which trace failed
    
                targetLocs.clear()
                i = 0
                return status, seqTime
    
            else:
                return 'FAIL', 0  # this is for 'padding' purposes since we must build a list     with the same dimension as the rows in the final df
    
        return drawOnPlot
    
    
    def savePlot(output_path, groups, enable_rmtree):
        """
        Saves the current matplotlib figure as a png file.
        :param output_path: output path to save the plots
        :param groups: this is a pandas Series that contain identifiers and will be used to     name the file
        :param enable_rmtree: flag to determine if file tree should be deleted
        :return: path to the plot save location
        """
    
        temp = dict(groups.loc['dut':'serial_number'].apply(
            str))  # directory name identifiers
        capturesPath = output_path / ('_'.join(
            temp.values()) + ' captures') / f'{groups.runid}'  # directory naming
        path_exists = capturesPath.exists()  # this is a flag
    
        # if the save directory already exists with plots generated from previous runs, delete     the filetree
        # and make a new save directory. This ensures nothing is overwritten and the script     runs quicker
        if path_exists and enable_rmtree:
            rmtree(capturesPath.parent)
            capturesPath.mkdir(parents=True)
        elif not path_exists:
            capturesPath.mkdir(parents=True)
    
        items = list(temp.keys())
        items.append('runid')
        items.append('capture')
        fig_name = dict(
            groups.drop(items).apply(str))  # plot fig_name is the test matrix inputs
        temp = fig_name.values()  # plot save name identifiers
        file = capturesPath / (f'capture{groups.capture}_' + (
                '_'.join(temp) + '.png'))  # plot save naming
    
        # format the plot fig_name
        titlestr = ''
        j = 1
        for key, val in fig_name.items():
            titlestr = titlestr + f'{key} --> {val:7}'
            if j % 2 == 0:
                titlestr = titlestr + '\n'
    
            j += 1
    
        ax = plt.gca()
    
        # save the plot
        ax.set_title(titlestr,
                     fontdict={'family': 'serif', 'color': 'darkblue', 'size': 10},
                     pad=35, loc='center',
                     va='baseline')
        plt.savefig(file, format='png', dpi=200)
        ax.lines = []
    
        plt.clf()
        gc.collect()
        return file
    
    
    def df2excel(df, traceNums, save_addresses, outputPath, name):
        """
        Writes a DataFrame to an excel sheet.
        :param df: pandas DataFrame to be written to an excel sheet
        :param traceNums: number of unique traces in the DataFrame
        :param save_addresses: list containing the save addresses of the plots generated
        :param outputPath: path to where the excel sheet should be saved
        :param name: name of the excel sheet
        """
    
        # NOTE: if columns are added or removed from the the final dataframe that will be     written to the excel sheet,
        #       the formatting rules must accommodate this change.
    
        thin = Side(border_style='thin', color='000000')
        lastcol = df.columns.shape[0] + 1  # this is the last column in the df
    
        # Writing dataframe to an excel sheet
        datapath = outputPath / f'{name}_results.xlsx'
        output_path = ExcelWriter(datapath, engine='openpyxl')
        df.to_excel(output_path, sheet_name='Results')
        output_path.save()
    
        # Make FAIL appear as red and PASS appear as green
        wb = load_workbook(datapath)
        ws = wb['Results']
        redFill = PatternFill(bgColor='FF0000', fill_type='solid')
        greenFill = PatternFill(bgColor='00FF00', fill_type='solid')
        dxf1 = DifferentialStyle(fill=redFill)
        dxf2 = DifferentialStyle(fill=greenFill)
        rule1 = Rule(operator='containsText', type='containsText', text='FAIL',
                     dxf=dxf1)
        rule2 = Rule(operator='containsText', type='containsText', text='PASS',
                     dxf=dxf2)
        letter = _get_column_letter(
            lastcol - 1)  # letter of the pass/fail column in the excel sheet
        rule1.formula = [f'NOT(ISERROR(SEARCH("FAIL", {letter}2)))']
        rule2.formula = [f'NOT(ISERROR(SEARCH("PASS", {letter}2)))']
        ws.conditional_formatting.add(f'{letter}2:{letter}{df.shape[0]}', rule1)
        ws.conditional_formatting.add(f'{letter}2:{letter}{df.shape[0]}', rule2)
    
        # add plots column to the excel sheet
        letter = _get_column_letter(
            lastcol + 1)  # letter of the plots column in the excel sheet
        cell = f'{letter}1'
        ws[cell] = 'plots'
        ws[cell].font = Font(bold=True)
        ws[cell].alignment = Alignment(vertical='top', horizontal='center')
        ws[cell].border = Border(bottom=thin)
    
        saveLoc = 0
        i = 2
        while i < df.shape[0]:
            # merge the pass/fail cells
            letter = _get_column_letter(
                lastcol - 1)  # letter of the pass/fail column in the excel sheet
            ws.merge_cells(f'{letter}{i}:{letter}{i + traceNums - 1}')
            top_left_cell = ws[f'{letter}{i}']
            top_left_cell.alignment = Alignment(horizontal='center',
                                                vertical='center')
    
            # merge the delta cells
            letter = _get_column_letter(
                lastcol)  # letter of the delta column in the excel sheet
            ws.merge_cells(f'{letter}{i}:{letter}{i + traceNums - 1}')
            top_left_cell = ws[f'{letter}{i}']
            top_left_cell.alignment = Alignment(horizontal='center',
                                                vertical='center')
    
            # merge the plot location cells
            letter = _get_column_letter(lastcol + 1)
            top_left_cell = ws[f'{letter}{i}']
            top_left_cell.hyperlink = str(
                save_addresses[saveLoc].resolve())  # location to the plot
            top_left_cell.value = save_addresses[saveLoc].name
            top_left_cell.style = 'Hyperlink'
            ws.merge_cells(f'{letter}{i}:{letter}{i + traceNums - 1}')
            top_left_cell.alignment = Alignment(horizontal='center',
                                                vertical='center')
    
            # Add thin underlines to make the results look cleaner
            ws[
                f'{_get_column_letter(lastcol - 2)}{i + traceNums - 1}'].border = Border(
                bottom=thin)
            ws[
                f'{_get_column_letter(lastcol - 1)}{i + traceNums - 1}'].border = Border(
                bottom=thin)
            ws[f'{_get_column_letter(lastcol)}{i + traceNums - 1}'].border = Border(
                bottom=thin)
            ws[
                f'{_get_column_letter(lastcol + 1)}{i + traceNums - 1}'].border = Border(
                bottom=thin)
    
            saveLoc += 1
            i += traceNums
    
        # Save sheet formatting
        wb.save(datapath)
        wb.close()
    
        # auto fit the column widths using pywin32
        excel = win32.Dispatch('Excel.Application')
        wb = excel.Workbooks.Open(datapath)
        excel.Worksheets('Results').Activate()
        ws = excel.ActiveSheet
        ws.Columns.AutoFit()
        wb.Close(SaveChanges=True)
        excel.Application.Quit()
    

# **************************************************************
# Main
# **************************************************************

# read in user input
try:
    userInput, dataCSV, configs = open_input_file(USER_INPUT_FILE, SHEET)
    raw_data, testpoints, nominalVals, targets, channel_nums = read_userInput(
        userInput, dataCSV, configs)

except Exception as error:
    print(error)
    sys.exit(
        1)  # if there are errors, display the error to the user and terminate the program

numoftraces = len(testpoints)
targetVals = list()
for i, target in enumerate(targets):
    if target[1] == 'p':  # if target mode is a percentage
        targetVal = nominalVals[i] * target[
            0]  # nom * percentage (e.g 12 * 0.85)
    else:  # else if target mode is a voltage level
        targetVal = target[0]
    targetVals.append(targetVal)

print("TESTPOINTS:", testpoints)
print("CORRESPONDING NOMINAL VALUES:", nominalVals)

# filter raw dataframe
plotDF = filterDf(raw_data)
# ***************************************************************

# save location
outputPath = Path(input(
    f'Enter a valid path to save output files (leave field empty for default path: {DEFAULT_OUTPUT_PATH.resolve()})\n> '))
if outputPath == '':
    path = DEFAULT_OUTPUT_PATH
if not outputPath.exists():
    try:
        outputPath.mkdir(parents=True)
    except:
        print("Path is not valid. Using default path instead.")
        path = DEFAULT_OUTPUT_PATH
# ***************************************************************

save_addresses = list()  # empty list to hold save addresses of plots
increment = raw_data['capture_json_x_increment'].iloc[0]  # delta t

print("Plotting...")
fig = plt.figure(dpi=200, constrained_layout=True)  # create figure

# build and configure an empty plot
legendCols = numoftraces if numoftraces <= 4 else int(
    (numoftraces + 1) / 2)  # for plotting purposes
status = list()
seqTimes = list()
i = 0  # counter to keep track of how many waveform_names have been read
for index, row_dict in tqdm(plotDF.iterrows(), total=plotDF.shape[0]):
    trace = row_dict['testpoint']
    if trace in testpoints:  # only read rows that contain traces specified by the user
        yvals = read_waveform(
            row_dict['waveform'])  # read data to be plotted into a vector
        traceIndex = testpoints.index(
            trace)  # this is the index of the trace in the order specified by the user
        loc = targetLoc(yvals, targetVals[
            traceIndex])  # find where traces reaches its target
    else:  # or else drop the rows
        plotDF.drop(index, axis=0, inplace=True)
        continue
    if i % numoftraces == 0:  # update timestamps vector after numoftraces lines have been read
        # build timestamps vector
        timestamps, step = np.linspace(-1 * (loc * increment), (
                (RECORD_LENGTH * increment) - (loc * increment)),
                                       RECORD_LENGTH, False, retstep=True)
        drawOnPlot = makePlot(testpoints, targetVals, increment,
                              legendCols)  # all plotting will be handled via the drawOnPlot function pointer

    i += 1  # update how many waveform_names have been read
    stat, seqTime = drawOnPlot(trace, timestamps, yvals, loc, traceIndex,
                               i == numoftraces)  # plot the yvals with respect to the timestamp values
    status.append(stat)
    seqTimes.append(seqTime)
    if i == numoftraces:  # after numoftraces have been read, reset counter i and save plot
        i = 0
        save_address = savePlot(outputPath, row_dict.drop(['testpoint', 'waveform']),
                                (
                                        index < channel_nums))  # save the plot and store save address
        save_addresses.append(save_address)

plotDF.reset_index(drop=True, inplace=True)
plotDF = plotDF.join(
    pd.DataFrame({'Pass/Fail': status, 'sequencing time (ms)': seqTimes}).shift(
        -1 * (numoftraces - 1)))
namelist = plotDF.loc[0, 'dut':'serial_number'].apply(str)  # device information
name = '_'.join(namelist)  # name of the results excel sheet
plt.close('all')
print("Generating excel file...")
df2excel(plotDF, numoftraces, save_addresses, outputPath.resolve(),
         name + '_sequencing')  # write dataframe to an excel sheet
print("FINISHED")
print(f"Results location: {outputPath.resolve()}")
'''
