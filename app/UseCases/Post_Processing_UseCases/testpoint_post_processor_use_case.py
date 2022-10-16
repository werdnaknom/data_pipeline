from __future__ import annotations
import typing as t
from collections import OrderedDict
from pathlib import Path

import pandas as pd

import matplotlib.pyplot as plt

from app.shared.Requests.requests import ValidRequestObject
from app.shared.Responses.response import ResponseSuccess
from app.shared.UseCase.usecase import UseCase
from app.Repository.repository import Repository, MongoRepository

from app.shared.Entities import WaveformEntity

from app import globalConfig

BASE_PATH = globalConfig.RESULTS_FOLDER


class TestpointPostProcessingRequestObject(ValidRequestObject):
    waveform_ids: t.List[str]
    test_name: str = None
    DF_SPEC_MIN: str = None
    DF_SPEC_MAX: str = None
    BASE_PATH = Path(BASE_PATH)

    def __init__(self, waveform_ids: t.List[str]):
        self.waveform_ids = waveform_ids

    @classmethod
    def from_dict(cls, adict) -> TestpointPostProcessingRequestObject:
        return cls(**adict)

    def make_save_paths(self, filter_tuple: t.Tuple[str],
                        waveform_names: t.List[str], testname: str = "") -> \
            t.List[Path]:
        path = self.BASE_PATH
        for key in filter_tuple:
            path = path.joinpath(str(key))

        if not path.exists():
            path.mkdir(parents=True)  # make parents too if they do not exist

        save_plots = []
        for wf_id in waveform_names:
            plot_file_name = self.testpoint_filename(waveform_id=wf_id,
                                                     testname=testname)
            save_plots.append(path.joinpath(plot_file_name))
        return save_plots

    def _spec_min(self, df: pd.DataFrame) -> float:
        spec_min_series = df[self.DF_SPEC_MIN]
        assert len(spec_min_series.unique()) == 1, "SPEC MIN must be unique, " \
                                                   f"{spec_min_series.unique()},"

        return spec_min_series.values[0]

    def _spec_max(self, df: pd.DataFrame) -> float:
        spec_max_series = df[self.DF_SPEC_MAX]
        assert len(spec_max_series.unique()) == 1, "SPEC MAX must be unique, " \
                                                   f"{spec_max_series.unique()}"
        return spec_max_series.values[0]

    def testpoint_filename(self, waveform_id, testname: str = ""):
        if testname:
            filename = f"{testname}_{waveform_id}.png"
        else:
            filename = f"{waveform_id}.png"
        return filename

    def _save_paths(self, plot_individual: bool, filter_tuple: t.Tuple[str],
                    waveform_ids: pd.Series) -> t.List[Path]:
        if plot_individual:
            plot_paths = self.make_save_paths(
                filter_tuple=filter_tuple, waveform_names=waveform_ids,
                testname=self.test_name)
        else:
            wf_name = waveform_ids.iloc[0]
            wf_name = wf_name[:wf_name.find("auxtomain") - 1]
            combined_name = f"{wf_name}_{filter_tuple[-1]}_combined"
            path = self.make_save_paths(filter_tuple=filter_tuple,
                                        waveform_names=[combined_name],
                                        testname=self.test_name)
            plot_paths = [path[0] for _ in range(len(waveform_ids))]

        return plot_paths


class TestPointPostProcessorUseCase(UseCase):
    repo: Repository
    sheet_name: str
    waveform_test: bool = True

    def __init__(self, repo: Repository):
        self.repo = repo

    def process_request(self,
                        request_object: TestpointPostProcessingRequestObject) \
            -> ResponseSuccess:
        result_df = self.post_process(request_object=request_object)

        return ResponseSuccess(value=result_df)

    def post_process(self,
                     request_object: TestpointPostProcessingRequestObject) \
            -> pd.DataFrame:
        raise NotImplementedError

    def load_waveforms(self, waveform_ids: t.List[str]) \
            -> t.List[WaveformEntity]:
        filter_list = [{"_id": id} for id in waveform_ids]
        wf_dicts = self.repo.find_many_waveforms(list_of_filters=filter_list)
        wf_entities = [WaveformEntity.from_dict(wf_dict) for wf_dict in
                       wf_dicts]
        return wf_entities

    def waveform_post_processing(self, waveforms: t.List[WaveformEntity],
                                 **kwargs) -> pd.DataFrame:
        '''

        @param waveforms: list of waveform entities to post process
        @param kwargs: additional keyword agruments
        @return:
        '''
        raise NotImplementedError

    @classmethod
    def convert_to_hyperlink(self, col: pd.Series):
        return col.apply(lambda x: f'=HYPERLINK("/{x}", "image")')

    def make_plot(self, **kwargs) -> plt.Figure:
        raise NotImplementedError

    def set_axes_labels(self, ax: plt.Subplot, xlabel: str = "Time (ms)",
                        ylabel: str = "Voltage (V)") -> None:
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

    def set_axes_ylabel(self, ax: plt.Subplot,
                        ylabel: str = "Voltage (V)") -> None:
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
        ax.text(xlim[0], spec_max, f"Spec Max ({spec_max})", c=COLOR)

        # spec min
        ax.axhline(y=spec_min, xmax=x_end, xmin=x_start, c=COLOR)
        ax.text(xlim[0], spec_min, f"Spec Min ({spec_min})", c=COLOR)

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

    def save_plot(self, save_path: Path, fig: plt.Figure):
        assert save_path.suffix == ".png", f"waveform savepath {save_path} " \
                                           f"must be a .png"
        fig.savefig(fname=save_path, dpi=200, format="png")
        plt.close(fig)
