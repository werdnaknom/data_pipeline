import typing as t
from collections import defaultdict, OrderedDict
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from app.UseCases.Post_Processing_UseCases.testpoint_post_processor_use_case \
    import TestpointPostProcessingRequestObject, TestPointPostProcessorUseCase

from app.UseCases.Post_Processing_UseCases.waveform_min_max_processing \
    .min_max_results import TestPointMinMaxResult

from app.shared.Entities import WaveformEntity

plt.style.use("ggplot")


class MinMaxRequestObject(TestpointPostProcessingRequestObject):
    test_name: str = "MinMax"
    spec_max: float
    spec_min: float
    plot_individual: bool = True
    plot_paths: t.List[Path]
    DF_SPEC_MIN: str = "spec_min"
    DF_SPEC_MAX: str = "spec_max"
    DF_WAVEFORM_ID: str = "waveform_id"

    def __init__(self, df: pd.DataFrame, filter_tuple: t.Tuple[str],
                 plot_individual: bool = True):
        self.spec_min = self._spec_min(df=df)
        self.spec_max = self._spec_max(df=df)
        self.plot_individual = plot_individual

        waveform_ids = df[self.DF_WAVEFORM_ID]
        super(MinMaxRequestObject, self).__init__(waveform_ids=waveform_ids)

        self.plot_paths = self._save_paths(plot_individual=plot_individual,
                                           waveform_ids=waveform_ids,
                                           filter_tuple=filter_tuple)


class TestpointMinMaxProcessingUseCase(TestPointPostProcessorUseCase):

    def post_process(self, request_object: MinMaxRequestObject) -> \
            pd.DataFrame:

        waveform_entities = self.load_waveforms(
            waveform_ids=request_object.waveform_ids)
        if (not waveform_entities) or (waveform_entities[0].edge):
            # If there are no waveforms or if the waveform is an EDGE rail
            return pd.DataFrame()

        wf_result_df = self.waveform_post_process(waveforms=waveform_entities,
                                                  spec_max=request_object.spec_max,
                                                  spec_min=request_object.spec_min)

        wf_paths = self.waveform_plotting(waveforms=waveform_entities,
                                          individual=request_object.plot_individual,
                                          plot_paths=request_object.plot_paths,
                                          spec_min=request_object.spec_min,
                                          spec_max=request_object.spec_max)

        wf_result_df["Plot"] = wf_paths

        if not request_object.plot_individual:
            # Summarize the results into a single series
            tp = TestPointMinMaxResult()
            wf_result_df = tp.flatten(df=wf_result_df)
            wf_result_df["Plot"] = wf_paths[0]

        wf_result_df["Plot"] = self.convert_to_hyperlink(
            col=wf_result_df["Plot"])

        return wf_result_df

    def waveform_post_process(self, waveforms: t.List[WaveformEntity],
                              spec_min: float, spec_max: float) -> pd.DataFrame:
        assert len(waveforms) > 0, "Waveforms must not be empty!"
        results = []
        for waveform in waveforms:
            wf_result = TestPointMinMaxResult().passfail(entity=waveform,
                                                         spec_min=spec_min,
                                                         spec_max=spec_max)
            results.append(wf_result)
        result_df = pd.DataFrame(results, columns=list(wf_result.keys()),
                                 index=[i for i in range(len(results))])

        return result_df

    def waveform_plotting(self, waveforms: t.List[WaveformEntity],
                          plot_paths: t.List[Path], individual: bool,
                          spec_min: float, spec_max: float) -> t.List[Path]:
        assert len(waveforms) > 0, "Waveforms must not be empty!"

        if individual:
            for wf, path in zip(waveforms, plot_paths):
                fig = self.make_plot(waveforms=[wf], spec_min=spec_min,
                                     spec_max=spec_max, testpoint=wf.testpoint)
                self.save_plot(save_path=path, fig=fig)
                assert path.exists(), "waveform should have been saved, " \
                                      f"but doesn't exist? {path}"

            return plot_paths
        else:
            fig = self.make_plot(waveforms=waveforms, spec_min=spec_min,
                                 spec_max=spec_max,
                                 testpoint=waveforms[0].testpoint)
            self.save_plot(save_path=plot_paths[0], fig=fig)
            return [plot_paths[0] for _ in range(len(waveforms))]

    def make_plot(self, waveforms: t.List[WaveformEntity],
                  spec_min: float, spec_max: float,
                  testpoint: str):
        assert len(waveforms) > 0, "to make a plot you need more than 0 " \
                                   f"waveforms! {self.__class__.__name__}"

        fig, axes = plt.subplots(2, 1, figsize=(10, 10))

        fig.suptitle(testpoint)

        full_wf_ax = axes[0]
        zoom_ax = axes[1]
        min_ss_loc = np.inf
        max_ss_loc = -np.inf
        ymax = -np.inf
        zoomed_ymax = -np.inf
        zoomed_ymin = np.inf

        for wf in waveforms:
            # WF Details
            x_end = wf.x_axis_in_milliseconds()[-1]
            steady_state_loc = wf.x_axis_in_milliseconds()[
                wf.steady_state_index()]

            # Incase there are multiple waveforms
            min_ss_loc = np.min([min_ss_loc, steady_state_loc])
            max_ss_loc = np.max([max_ss_loc, steady_state_loc])

            # Full WF Image:
            full_wf_ax.plot(wf.x_axis_in_milliseconds(), wf.y_axis(), c='b')
            ymax = max([ymax] + wf.y_axis())

            # Zoomed WF Image:
            wf_ss_min = max(0, wf.steady_state_index() - 5)
            zoomed_y = wf.y_axis()[wf_ss_min:]
            zoomed_x = wf.x_axis_in_milliseconds()[wf_ss_min:]
            zoom_ax.plot(zoomed_x, zoomed_y, c="b")

            raw_zoomed = wf.y_axis()[wf.steady_state_index():]
            zoomed_ymax = max([zoomed_ymax] + raw_zoomed)
            zoomed_ymin = min([zoomed_ymin] + raw_zoomed)

        # Add X and Y Axis labels
        self.set_axes_labels(ax=full_wf_ax, ylabel="Voltage (V)",
                             xlabel="Time (ms)")
        self.set_axes_labels(ax=zoom_ax, ylabel="Voltage (V)",
                             xlabel="Time (ms)")
        # Place steady state lines
        vertical_line_max = ymax * 5
        if max_ss_loc == min_ss_loc:
            self.axes_vertical_line(ax=full_wf_ax,
                                    xloc=max_ss_loc,
                                    label="Steady State",
                                    ymax=vertical_line_max)
            self.axes_vertical_line(ax=zoom_ax, xloc=max_ss_loc,
                                    label="Steady State",
                                    ymax=vertical_line_max)
        else:
            self.axes_vertical_line(ax=full_wf_ax,
                                    xloc=max_ss_loc,
                                    label="Max Steady State",
                                    ymax=vertical_line_max)
            self.axes_vertical_line(ax=full_wf_ax,
                                    xloc=min_ss_loc,
                                    label="Min Steady State",
                                    ymax=vertical_line_max)
            self.axes_vertical_line(ax=zoom_ax, xloc=max_ss_loc,
                                    label="Max Steady State",
                                    ymax=vertical_line_max)
            self.axes_vertical_line(ax=zoom_ax, xloc=min_ss_loc,
                                    label="Min Steady State",
                                    ymax=vertical_line_max)

        # Add Spec lines
        try:
            self.axes_add_max_min(ax=full_wf_ax, spec_min=spec_min,
                                  spec_max=spec_max, x_end=x_end)
            self.axes_add_max_min(ax=zoom_ax, spec_min=spec_min,
                                  spec_max=spec_max, x_end=x_end)
        except AssertionError:
            print(wf)

        # Add Mean Tick
        wf_means = np.mean([wf.steady_state_mean for wf in waveforms])
        self.axes_add_y_tick(ax=full_wf_ax,
                             nominal_value=wf_means,
                             label="mean")
        self.axes_add_y_tick(ax=zoom_ax, nominal_value=wf_means,
                             label="mean")

        self.axes_add_y_tick(ax=zoom_ax, nominal_value=zoomed_ymax,
                             label="max")
        self.axes_add_y_tick(ax=zoom_ax, nominal_value=zoomed_ymin,
                             label="min")

        return fig
