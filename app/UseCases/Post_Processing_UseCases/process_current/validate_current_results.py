from __future__ import annotations

import string
import random
import typing as t
from collections import OrderedDict
from pathlib import Path
from dataclasses import dataclass
from app.shared.Results.results import Result

import matplotlib.pyplot as plt

import pandas as pd

from app.shared.Entities.entities import *


class CurrentProcessingResultEntity(Result):

    def add_result_from_dataframe_row(self):
        pass


@dataclass
class CurrentProcessResultRow:
    project_entity: ProjectEntity
    pba_entity: PBAEntity
    rework_entity: ReworkEntity
    submission_entity: SubmissionEntity
    runid_entity: RunidEntity
    capture_entity: WaveformCaptureEntity
    waveform_entity: WaveformEntity
    result: str
    result_reason: str
    image_location: str
    scope_image:str

    def to_result(self):
        result = OrderedDict()
        for entity in [self.project_entity, self.pba_entity,
                       self.rework_entity, self.submission_entity,
                       self.runid_entity, self.capture_entity,
                       self.waveform_entity]:
            result.update(entity.to_result())
        result['Result'] = self.result
        result['Result Reason'] = self.result_reason
        result['Image'] = self.path_str_to_excel_hyperlink(self.image_location,
                                                           "Result Image")
        result["Scope Image"] = self.path_str_to_excel_hyperlink(
            self.scope_image, "Scope Image")
        return result

    @classmethod
    def path_str_to_excel_hyperlink(cls, path_str: str, hyperlink_name) -> str:
        assert isinstance(path_str, str)
        hyperlink = f'=HYPERLINK("{path_str}", ' \
                    f'"{hyperlink_name}")'
        return hyperlink

    @classmethod
    def from_dataframe_row(cls, row: pd.Series, curr_wf: WaveformEntity,
                           result: str, result_reason: str,
                           image_str: str) -> CurrentProcessResultRow:
        pe = ProjectEntity.from_dataframe_row(row)
        pbae = PBAEntity.from_dataframe_row(row)
        re = ReworkEntity.from_dataframe_row(row)
        se = SubmissionEntity.from_dataframe_row(row)
        rune = RunidEntity.from_dataframe_row(row)
        ce = WaveformCaptureEntity.from_dataframe_row(row)
        scope_image = row["file_capture_capture.png"]
        we = curr_wf

        cprr = CurrentProcessResultRow(project_entity=pe, pba_entity=pbae,
                                       rework_entity=re, submission_entity=se,
                                       runid_entity=rune,
                                       capture_entity=ce, result=result,
                                       waveform_entity=we,
                                       result_reason=result_reason,
                                       image_location=image_str,
                                       scope_image=scope_image)

        return cprr

    def plot_waveforms(self, output_path: Path, waveforms: t.List[
        WaveformEntity]) -> str:
        plt.style.use('ggplot')

        png_path = output_path.with_suffix(suffix=".png")
        num_wfs = len(waveforms)

        fig, axes = plt.subplots(num_wfs, 1, figsize=(20, 20))
        if num_wfs == 1:
            axes = [axes]
        for ax, wf in zip(axes, waveforms):
            ax.plot(wf.x_axis(), wf.y_axis())
            ax.set_title(wf.testpoint)
            ax.set_xlabel("Time (ms)")
            if wf.units == "A":
                ax.set_ylabel("Current (A)")
            else:
                ax.set_ylabel("Voltage (V)")
        fig.tight_layout()
        plt.savefig(png_path, format="png")
        plt.close(fig)
        return str(png_path.resolve())
