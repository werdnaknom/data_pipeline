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
import pandas as pd
import pickle

from app.UseCases.Post_Processing_UseCases.post_processing_use_case import \
    PostProcessingUseCase, PostProcessingRequestObject
from app.shared.Entities import WaveformEntity
from app.UseCases.Post_Processing_UseCases.waveform_min_max_processing \
    .min_max_results import TestPointMinMaxResult

plt.style.use("ggplot")
WAVEFORM_DICT = t.NewType("WAVEFORM_DICT", t.Dict[str, t.List[WaveformEntity]])


class WaveformProcessingUseCase(PostProcessingUseCase):
    sheet_name = "WF Min-Max"
    EDGE_RAIL_COLUMN_HEADER = "edge_rail"
    SPEC_MAX_COLUMN_HEADER = "spec_max"
    SPEC_MIN_COLUMN_HEADER = "spec_min"
    EXPECTED_NOMINAL_COLUMN_HEADER = "expected_nominal"

    def _test_specific_columns(self):
        '''

        @return:
        return [self.EDGE_RAIL_COLUMN_HEADER, self.TRACE_ORDER_COLUMN_HEADER,
                self.POWER_ON_TIME_COLUMN_HEADER, self.TIME_DELTA_COLUMN_HEADER]
        '''
        return [self.EDGE_RAIL_COLUMN_HEADER, self.SPEC_MAX_COLUMN_HEADER,
                self.SPEC_MIN_COLUMN_HEADER,
                self.EXPECTED_NOMINAL_COLUMN_HEADER]

    def post_process(self, request_object: PostProcessingRequestObject) -> \
            pd.DataFrame:
        """
        The waveform validation test ensures the voltage waveform is within
        it's spec max/min values.

        @param request_object:
        @return:
        """
        # Filter raw dataframe

        filtered_df = self.filter_df(raw_df=request_object.df)

        results_df = self.make_results(filtered_df=filtered_df,
                                       request_object=request_object)

        return results_df

    def make_results(self, filtered_df: pd.DataFrame, request_object:
    PostProcessingRequestObject) -> pd.DataFrame:

        return self._make_results_df(filtered_df=filtered_df, merge_columns=[],
                                     request_object=request_object)

    def _make_results_df(self, filtered_df: pd.DataFrame,
                         merge_columns: t.List[str],
                         request_object: PostProcessingRequestObject) -> pd.DataFrame:
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
                if (entity is None) or (entity._id != row[header_id]):
                    update = True

                if update:
                    index = entities.index(entity)
                    # print(header_id, row_dict[header_id])
                    entity = query_funct(filters={"_id":
                                                      str(row[header_id])})[0]
                    entities[index] = entity

                result_row.update(entity.to_result())

            result_row = self.business_logic(row=row, result_row=result_row,
                                             last_entity=entity)
            result_row_df = pd.DataFrame(result_row, columns=result_row.keys(),
                                         index=[0])
            result_df = pd.concat([result_row_df, result_df], ignore_index=True)

        return result_df

    def business_logic(self, row: pd.Series, result_row: OrderedDict,
                       last_entity: WaveformEntity) -> OrderedDict:

        # Get Result
        testpoint_results = TestPointMinMaxResult().passfail(
            entity=last_entity,
            spec_min=row.spec_min,
            spec_max=row.spec_max
        )

        # Plot Waveform
        if last_entity.edge:
            spec_max = 15
            spec_min = 0
        else:
            spec_max = row.spec_max
            spec_min = row.spec_min
        fig = self.make_plot(waveforms=[last_entity],
                             testpoint=last_entity.testpoint,
                             spec_max=spec_max,
                             spec_min=spec_min)

        saved_path = self.save_testpoint_plot(result_dict=result_row,
                                              waveform_entity=last_entity,
                                              fig=fig)
        testpoint_results["Plot"] = str(saved_path.resolve())

        result_row.update(testpoint_results)

        return result_row

        '''
        # wf_results = WaveformResults()
        for df_filters, group_df in input_df.groupby(by=by):
            # Validate group_df
            testpoint, spec_min, spec_max, nominal = \
                self.validate_dataframe(df=group_df)

            waveform_list = self.load_waveforms(df=group_df)

            self.make_plot(waveform_names=waveform_list, spec_min=spec_min,
                           spec_max=spec_max, testpoint=testpoint)
        pass
        '''
        return row

    def make_plot(self, waveforms: t.List[WaveformEntity],
                  spec_min: float, spec_max: float,
                  testpoint: str):

        fig, axes = plt.subplots(2, 1, figsize=(20, 20))

        fig.suptitle(testpoint)

        full_wf_ax = axes[0]
        zoom_ax = axes[1]

        for wf in waveforms:
            # WF Details
            x_end = wf.x_axis_in_milliseconds()[-1]
            steady_state_loc = wf.x_axis_in_milliseconds()[
                wf.steady_state_index()]

            # Full WF Image:
            full_wf_ax.plot(wf.x_axis_in_milliseconds(), wf.y_axis(), c='b')
            self.set_axes_labels(ax=full_wf_ax, ylabel="Voltage (V)",
                                 xlabel="Time (ms)")
            self.axes_vertical_line(ax=full_wf_ax,
                                    xloc=steady_state_loc,
                                    label="Steady State",
                                    ymax=max(wf.y_axis()) * 1.1)
            self.axes_add_max_min(ax=full_wf_ax, spec_min=spec_min,
                                  spec_max=spec_max, x_end=x_end)
            self.axes_add_y_tick(ax=full_wf_ax,
                                 nominal_value=wf.steady_state_mean,
                                 label="mean")
            # Zoomed WF Image:
            wf_ss_min = max(0, wf.steady_state_index() - 5)
            zoomed_y = wf.y_axis()[wf_ss_min:]
            zoomed_x = wf.x_axis_in_milliseconds()[wf_ss_min:]
            zoom_ax.plot(zoomed_x, zoomed_y, c="b")
            self.set_axes_labels(ax=zoom_ax, ylabel="Voltage (V)",
                                 xlabel="Time (ms)")

            self.axes_vertical_line(ax=zoom_ax, xloc=steady_state_loc,
                                    label="Steady State",
                                    ymax=max(zoomed_y) * 1.1)

            self.axes_add_max_min(ax=zoom_ax, spec_min=spec_min,
                                  spec_max=spec_max, x_end=x_end)
            self.axes_add_y_tick(ax=zoom_ax, nominal_value=wf.steady_state_mean,
                                 label="mean")
            self.axes_add_y_tick(ax=zoom_ax, nominal_value=wf.steady_state_max,
                                 label="max")
            self.axes_add_y_tick(ax=zoom_ax, nominal_value=wf.steady_state_min,
                                 label="min")

        '''
        for wf in waveform_names:
            x_min = max(0, wf.steady_state_index() - 10)
            plt.plot(wf.x_axis_in_milliseconds()[x_min:], wf.y_axis()[x_min:])
            plt.title(testpoint)
            plt.axhline(y=spec_min, xmin=0,
                        xmax=wf.x_axis_in_milliseconds()[-1])
            plt.axhline(y=spec_max, xmin=0,
                        xmax=wf.x_axis_in_milliseconds()[-1])
            plt.axvline(x=wf.x_axis_in_milliseconds()[wf.steady_state_index()])
        '''

        return fig

    def validate_dataframe(self, df: pd.DataFrame) \
            -> t.Tuple[str, float, float, float]:
        # Validate group_df
        testpoint = df['testpoint'].unique()
        spec_min = df[self.SPEC_MIN_COLUMN_HEADER].unique()
        spec_max = df[self.SPEC_MAX_COLUMN_HEADER].unique()
        nominal = df[self.EXPECTED_NOMINAL_COLUMN_HEADER].unique()

        assert len(
            testpoint) == 1, f"testpoint should be unique (length 1) but was not, {testpoint}"
        assert len(
            spec_min) == 1, f"spec_min should be unique (length 1) for {testpoint} but was not, {spec_min}"
        assert len(
            spec_max) == 1, f"spec_max should be unique (length 1) for" \
                            f" {testpoint} but was not, {spec_max}"
        assert len(
            nominal) == 1, f"expected_nominal should be unique (length 1) for" \
                           f" {testpoint} but was not, {nominal}"

        testpoint = testpoint[0]
        spec_min = spec_min[0]
        spec_max = spec_max[0]
        nominal = nominal[0]

        return testpoint, spec_min, spec_max, nominal
