import typing as t
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from app.UseCases.Post_Processing_UseCases.capture_post_processor_use_case \
    import CapturePostProcessingRequestObject, CapturePostProcessorUseCase

from app.UseCases.Post_Processing_UseCases.process_current. \
    capture_current_results import CaptureCurrentResult, CaptureEdgePair

from app.shared.Entities import WaveformEntity


class CaptureCurrentRequestObject(CapturePostProcessingRequestObject):
    pairs: t.List[CaptureEdgePair]
    num_axes: int
    spec_max: float
    plot_path: Path
    test_name: str = "Current_Limit"
    DF_SPEC_MAX: str = "spec_max"
    DF_WAVEFORM_ID: str = "waveform_id"
    DF_EGDE_RAIL: str = "edge_rail"
    DF_ASSOCIATED_RAIL: str = "associated_rail"
    DF_CURRENT_RAIL: str = "current_rail"
    DF_MAX_POWER: str = "max_power"
    DF_TESTPOINT: str = "testpoint"

    def __init__(self, df: pd.DataFrame, filter_tuple: t.Tuple[str]):
        self.pairs = self._match_edge_pairs(df=df)
        self.num_axes = len(self.pairs)
        self.plot_path = self.make_save_path(filter_tuple=filter_tuple,
                                             testname=self.test_name)

    def _match_edge_pairs(self, df: pd.DataFrame) -> t.List[CaptureEdgePair]:
        pairs = []
        current_df = df[df[self.DF_CURRENT_RAIL]]

        for current_testpoint, groupdf in current_df.groupby(
                by=self.DF_TESTPOINT):
            voltage_testpoint = groupdf[self.DF_ASSOCIATED_RAIL].iloc[0]

            current_wf_ids = groupdf[groupdf[self.DF_TESTPOINT] ==
                                     current_testpoint][self.DF_WAVEFORM_ID]
            voltage_wf_ids = df[df[self.DF_TESTPOINT] == voltage_testpoint][
                self.DF_WAVEFORM_ID]
            spec_max = groupdf[self.DF_SPEC_MAX].iloc[0]
            max_power = groupdf[self.DF_MAX_POWER].iloc[0]
            pair = CaptureEdgePair(current_rail_ids=current_wf_ids,
                                   voltage_rail_ids=voltage_wf_ids,
                                   spec_max=spec_max, max_power=max_power)
            pairs.append(pair)
        return pairs


class CaptureCurrentProcessingUseCase(CapturePostProcessorUseCase):

    def post_process(self, request_object: CaptureCurrentRequestObject) -> \
            pd.DataFrame:
        result_df = pd.DataFrame()
        for pair in request_object.pairs:
            current_wfs = self.load_waveforms(
                waveform_ids=pair.current_rail_ids)
            voltage_wfs = self.load_waveforms(
                waveform_ids=pair.voltage_rail_ids)

            result_dict, result_obj = self.capture_post_processing(
                current_wfs=current_wfs,
                voltage_wfs=voltage_wfs,
                edge_pair=pair, )

            wf_name = current_wfs[0].testpoint
            save_path = request_object.plot_path
            save_path = save_path.with_name(
                name=f"{wf_name}_{save_path.name}").with_suffix(
                ".png")

            capture_path = self.capture_plotting(current_wfs=current_wfs,
                                                 voltage_wfs=voltage_wfs,
                                                 power_wfs=result_obj.power_waveforms(),
                                                 current_spec=pair.spec_max,
                                                 power_spec=pair.max_power,
                                                 save_path=save_path)

            result_dict["Plot"] = self.convert_to_hyperlink(col=pd.Series([
                capture_path]))

            pair_df = pd.DataFrame(result_dict, columns=list(
                result_dict.keys()), index=[0])
            result_df = pd.concat([result_df, pair_df], ignore_index=True)
        return result_df

    def capture_post_processing(self, current_wfs: t.List[WaveformEntity],
                                voltage_wfs: t.List[WaveformEntity],
                                edge_pair: CaptureEdgePair) -> \
            t.Tuple[t.OrderedDict, CaptureCurrentResult]:
        '''

        @param current_wfs:
        @param voltage_wfs:
        @param edge_pair:
        @return:
        '''

        pair_result = CaptureCurrentResult(voltage_wfs=voltage_wfs,
                                           current_wfs=current_wfs,
                                           current_spec_max=edge_pair.spec_max,
                                           max_power=edge_pair.max_power)
        pair_dict = pair_result.passfail()

        return pair_dict, pair_result

    def capture_plotting(self, current_wfs: t.List[WaveformEntity],
                         voltage_wfs: t.List[WaveformEntity],
                         power_wfs: t.List[np.array], current_spec: float,
                         power_spec: float, save_path: Path) -> Path:

        save_title = save_path.name.replace("_", " ")
        plot_title = f"{current_wfs[0].testpoint} {save_title}"

        fig = self.make_plot(current_wfs=current_wfs, voltage_wfs=voltage_wfs,
                             power_wfs=power_wfs, current_spec=current_spec,
                             power_spec=power_spec, plot_title=plot_title)
        self.save_and_close_plot(save_path=save_path, fig=fig)

        assert save_path.exists(), "waveform should have been saved, " \
                                   f"but doesn't exist? {save_path}"
        return save_path

    def make_plot(self, current_wfs: t.List[WaveformEntity],
                  voltage_wfs: t.List[WaveformEntity],
                  power_wfs: t.List[np.array], current_spec: float,
                  power_spec: float, plot_title: str) -> plt.Figure:
        fig, axes = plt.subplots(3, 1, sharex='col', figsize=(10, 10))

        voltage_ax = axes[0]
        current_ax = axes[1]
        power_ax = axes[2]

        fig.suptitle(plot_title)

        multiple = len(current_wfs) > 1

        for current_wf, voltage_wf in zip(current_wfs, voltage_wfs):
            if multiple:
                current_ax.plot(current_wf.x_axis_in_milliseconds(),
                                current_wf.y_axis())

                voltage_ax.plot(voltage_wf.x_axis_in_milliseconds(),
                                voltage_wf.y_axis())
            else:
                current_ax.plot(current_wf.x_axis_in_milliseconds(),
                                current_wf.y_axis(), color='orange')

                voltage_ax.plot(voltage_wf.x_axis_in_milliseconds(),
                                voltage_wf.y_axis(), color='b')

        xend = current_wfs[0].x_axis_in_milliseconds()[-1]

        current_ax.set_ylabel("Current (A)")  # , color="b")
        voltage_ax.set_ylabel('Voltage (V)')  # , color='b')

        try:
            self.axes_add_max(ax=current_ax, spec_max=current_spec,
                              x_end=xend,
                              text=f"Current Spec Max ({current_spec}A)")
        except AssertionError:
            print(
                f"Current spec assertion on {current_wf} missed! Current spec "
                f"was: {current_spec}.")

        for power_wf in power_wfs:
            if multiple:
                power_ax.plot(current_wfs[0].x_axis_in_milliseconds(), power_wf)
            else:
                power_ax.plot(current_wfs[0].x_axis_in_milliseconds(),
                              power_wf, color='purple')

        self.set_axes_labels(ax=power_ax, ylabel="Power (W)",
                             xlabel="Time (ms)")
        try:
            self.axes_add_max(ax=power_ax, spec_max=power_spec,
                              x_end=xend,
                              text=f"Power Spec Max ({power_spec}W)")
        except AssertionError:
            print(
                f"Current spec assertion on {current_wf} missed! Current spec "
                f"was: {current_spec}.")

        fig.tight_layout()

        return fig
