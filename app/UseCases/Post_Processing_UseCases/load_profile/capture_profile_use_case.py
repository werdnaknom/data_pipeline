import typing as t
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from app.UseCases.Post_Processing_UseCases.capture_post_processor_use_case \
    import CapturePostProcessingRequestObject, CapturePostProcessorUseCase

from app.UseCases.Post_Processing_UseCases.load_profile. \
    capture_profile_results import CaptureTestPoint, CaptureProfileResult

from app.shared.Entities import WaveformEntity


class CaptureProfileRequestObject(CapturePostProcessingRequestObject):
    testpoints: t.Dict[str, CaptureTestPoint]
    plot_path: Path
    test_name: str = "Load_Profile"
    DF_WAVEFORM_ID: str = "waveform_id"
    DF_TESTPOINT: str = "testpoint"
    DF_SPEC_MAX: str = "spec_max"
    DF_SPEC_MIN: str = "spec_min"
    DF_EDGE_RAIL: str = "edge_rail"

    def __init__(self, df: pd.DataFrame, filter_tuple: t.Tuple[str]):
        self.testpoints = self._create_capture_testpoints(df=df)
        self.plot_path = self.make_save_path(filter_tuple=filter_tuple,
                                             testname=self.test_name)

    def _create_capture_testpoints(self, df: pd.DataFrame) \
            -> t.Dict[str, CaptureTestPoint]:
        testpoints = {}
        for testpoint in df[self.DF_TESTPOINT].unique():
            testpoint_df = df[df[self.DF_TESTPOINT] == testpoint]
            edge = testpoint_df[self.DF_EDGE_RAIL].iloc[0]
            waveform_ids = testpoint_df[self.DF_WAVEFORM_ID]
            spec_max = np.min(testpoint_df[self.DF_SPEC_MAX])
            spec_min = np.max(testpoint_df[self.DF_SPEC_MIN])

            testpoint_obj = CaptureTestPoint(testpoint=testpoint,
                                             waveform_ids=waveform_ids,
                                             spec_max=spec_max,
                                             spec_min=spec_min,
                                             edge=edge)
            testpoints[testpoint] = testpoint_obj
        return testpoints


class CaptureProfileProcessingUseCase(CapturePostProcessorUseCase):

    def post_process(self, request_object: CaptureProfileRequestObject) -> \
            pd.DataFrame:
        result_df = pd.DataFrame()
        testpoint_dict = request_object.testpoints
        for testpoint in testpoint_dict.values():
            waveforms = self.load_waveforms(testpoint.waveform_ids)
            testpoint.waveforms = waveforms

            testpoint_result = self.capture_post_processing(
                testpoint_obj=testpoint)
            testpoint_df = pd.DataFrame(testpoint_result,
                                        columns=list(testpoint_result.keys()),
                                        index=[0])
            result_df = pd.concat([result_df, testpoint_df], ignore_index=True)

        capture_paths = self.capture_plotting(testpoint_dict,
                                              plot_path=request_object.plot_path)

        result_df["Plot"] = self.convert_to_hyperlink(col=pd.Series(
            capture_paths))

        return result_df

    def capture_post_processing(self,
                                testpoint_obj: CaptureTestPoint) -> \
            t.OrderedDict:
        '''
        @param testpoint:
        @return:
        '''

        testpoint_dict = testpoint_obj.passfail()

        return testpoint_dict

    def capture_plotting(self, testpoint_dict: t.Dict[str, CaptureTestPoint],
                         plot_path: Path) -> t.List[Path]:

        title = plot_path.name.replace("_", " ")

        fig = self.make_plot(testpoint_dict=testpoint_dict, plot_title=title)
        self.save_and_close_plot(save_path=plot_path, fig=fig)

        assert plot_path.exists(), "waveform plot should have been saved, " \
                                   f"but doesn't exist? {plot_path}"
        save_paths = [plot_path for _ in range(len(testpoint_dict))]
        return save_paths

    def make_plot(self, testpoint_dict: t.Dict[str, CaptureTestPoint],
                  plot_title: str) -> plt.Figure:
        num_plots = len(testpoint_dict)

        fig, axes = plt.subplots(num_plots, 1, sharex='col', figsize=(10, 20))
        fig.suptitle(plot_title)
        self.set_axes_xlabel(ax=axes[-1], xlabel="Time (ms)")

        for ax, (testpoint_name, testpoint_obj) in zip(axes,
                                                       testpoint_dict.items()):
            ax.set_title(testpoint_name)
            testpoint_wfs = testpoint_obj.waveforms
            if len(testpoint_wfs) == 0:
                continue
            if len(testpoint_wfs) > 1:
                multiple = True
            else:
                multiple = False

            for wf in testpoint_wfs:
                xaxis = wf.x_axis_in_milliseconds()
                yaxis = wf.y_axis()
                if multiple:
                    ax.plot(xaxis, yaxis)
                else:
                    ax.plot(xaxis, yaxis, color="b")

            xend = xaxis[-1]
            # set yaxis label
            if testpoint_wfs[0].units == "A":
                self.set_axes_ylabel(ax=ax, ylabel="Current (A)")
                self.axes_add_max(ax=ax, spec_max=testpoint_obj.spec_max,
                                  text=f"Spec Max ({testpoint_obj.spec_max}A)",
                                  x_end=xend)
            else:
                self.set_axes_ylabel(ax=ax, ylabel="Voltage (V)")
                wf_ss_loc = wf.x_axis_in_milliseconds()[wf.steady_state_index()]
                if not testpoint_obj.edge:
                    try:
                        self.axes_add_max_min(ax=ax,
                                              spec_min=testpoint_obj.spec_min,
                                              spec_max=testpoint_obj.spec_max,
                                              x_end=xend, units="V")
                        self.axes_set_ylim_from_specs(ax=ax,
                                                      spec_max=testpoint_obj.spec_max,
                                                      spec_min=testpoint_obj.spec_min)
                    except AssertionError:
                        print(f"{testpoint_obj} doesn't have a spec min or "
                              f"spec max! {testpoint_obj.spec_min}, "
                              f"{testpoint_obj.spec_max}")
                wf_max = round(testpoint_obj.wf_max, 2)
                wf_mean = round(testpoint_obj.wf_mean, 2)
                wf_min = round(testpoint_obj.wf_min, 2)
                self.axes_add_y_tick(ax=ax, nominal_value=wf_max,
                                     label="max")
                self.axes_add_y_tick(ax=ax, nominal_value=wf_mean,
                                     label="mean")
                self.axes_add_y_tick(ax=ax, nominal_value=wf_min,
                                     label="min")
        fig.tight_layout()

        return fig
