import pandas as pd
import os
from pathlib import Path

from app.shared.Entities.entities import *

from app.shared.Entities.file_entities import *

import matplotlib.pyplot as plt


class Result():
    sheet_name: str
    df: pd.DataFrame

    def __init__(self, sheet_name: str, dataframe: pd.DataFrame = None):
        if dataframe is None:
            self.df = pd.DataFrame()
        else:
            self.df = dataframe

        self.sheet_name = sheet_name

    def add_result(self, **kwargs):
        raise NotImplementedError

    def _append_index(self, rdict: OrderedDict):
        if self.df.empty:
            cols = list(rdict.keys())
            self.df = pd.DataFrame(rdict, columns=cols,
                                   index=[0])
        else:
            result = pd.Series(rdict)
            self.df = self.df.append(result, ignore_index=True)


class ScopePowerResult(Result):
    sheet_name = "Power Results"

    def __init__(self, dataframe: pd.DataFrame = None):
        super(ScopePowerResult, self).__init__(sheet_name=self.sheet_name,
                                               dataframe=dataframe)

    def add_result(self, power_entity: WaveformEntity, picture_location: str,
                   df_row: pd.Series, result: str, result_rationale: str):
        result_dict = OrderedDict()

        for entity in [RunidEntity, WaveformCaptureEntity, ProjectEntity,
                       PBAEntity, ReworkEntity, SubmissionEntity,
                       StatusFileEntity, TestRunFileEntity, CommentsFileEntity,
                       SystemInfoFileEntity, CaptureEnvironmentFileEntity]:
            e = entity.from_dataframe_row(df_row)
            result_dict.update(e.to_result())

        result_dict.update(power_entity.to_result())
        power_path = Path(os.environ.get('RESULTS_FOLDER'))
        plt_path = self.plot_entity(path=power_path, power_entity=power_entity,
                         spec_max=25.0)
        #print(plt_path.resolve(), type(plt_path.resolve()))
        result_dict['HyperLink'] = f'=HYPERLINK("{str(plt_path.resolve())}", ' \
                                   f'"HyperLink")'
        result_dict['Pass/Fail'] = result
        result_dict['Reason'] = result_rationale

        self._append_index(rdict=result_dict)


    def plot_entity(self, path: Path, power_entity: WaveformEntity,
                    spec_max: float) -> Path:
        file_fmt = "{runid}-{capture}_{testpoint}_{spec_max}{units}"
        filename = file_fmt.format(testpoint=power_entity.testpoint,
                                   spec_max=spec_max,
                                   units=power_entity.units,
                                   runid=power_entity.runid,
                                   capture=power_entity.capture)
        filename = filename.replace(".", "P") + ".png"
        file_path = path.joinpath(filename)
        # output = current_app.config['RESULTS_FOLDER']

        fig = plt.figure()
        x = power_entity.x_axis()
        xmin = x[power_entity.steady_state_index()]
        xmax = x[-1]

        plt.plot(power_entity.x_axis(), power_entity.y_axis())
        plt.hlines(y=spec_max, xmin=xmin, xmax=xmax, colors='r',
                   linestyles='dashdot',
                   label=f"Spec Max Limit Line ({spec_max}{power_entity.units})")
        plt.ylim(power_entity.min - 1, max(power_entity.max, spec_max) + 1)
        plt.legend()
        plt.savefig(file_path, format="png")
        plt.close(fig)

        return file_path
