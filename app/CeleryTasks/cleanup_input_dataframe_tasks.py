import typing as t
from pathlib import Path

from celery import Task

import pandas as pd
import numpy as np

from celery_worker import celeryapp

from app.CeleryTasks.celery_task_base_class import CeleryTaskBaseClass


class InputDataFrameCleanup(CeleryTaskBaseClass):
    """
    Take raw data input file and combine with user_input XLSX.  There are
    several pages in the XLSX file, which will each be combined into the full dataframe.
        - Edge Channels -- Indicates which rails are BOARD INPUT channels
        (voltage and current) and any max current/power requirements for
        those rails.
        - On-Board Rails -- Indicates which rails are BOARD channels.
        Information about nominal value and spec min/max values.
        - Rails to Rename -- Any waveform_names that are mistyped or otherwise
        need to be cleaned up.
        - Sequencing -- Sequencing specific test information
        - Timing -- Timing specific test information

    """

    _file_prefix: str = "InputCleanup"
    SPEC_MAX: str = "spec_max"  # Max do not cross line
    SPEC_MIN: str = "spec_min"  # Minimum do not cross line
    EXPECTED_NOMINAL: str = "expected_nominal"  # Expected voltage
    # VALID_VOLTAGE: str = "valid_voltage"
    EDGE_RAIL: str = "edge_rail"  # Edge (True) or On-board (False) Rail
    MAX_POWER: str = "max_power"
    # What edge rail generates this signal (primarily voltage edge rails,
    # except for voltage edge rails where it's the current edge)
    ASSOCIATED_EDGE_RAIL: str = "associated_rail"
    CURRENT_RAIL: str = "current_rail"
    TESTPOINT: str = "testpoint"

    def read_config_update_data(self,
                                config_dict: t.OrderedDict[str, pd.DataFrame],
                                data_df: pd.DataFrame):
        raise NotImplementedError

    def run(self, config_path: str, data_path: str) -> str:
        config_dict: t.OrderedDict[str, pd.DataFrame] = \
            self.load_dataframe_from_xlsx(config_path)
        data_df = self.load_dataframe_from_csv(data_path)

        # init_size = data_df.shape

        # Updates data_df inplace
        self.read_config_update_data(config_dict=config_dict,
                                     data_df=data_df)

        # final_size = data_df.shape

        df_path = self.df_to_pickle(df=data_df)
        str_path = self.path_to_str(path=df_path)

        return str_path

    def load_dataframe_from_xlsx(self, xlsx_path: str) \
            -> t.OrderedDict[str, pd.DataFrame]:
        xlsx_path = Path(xlsx_path)
        file_suffix = ".xlsx"
        assert xlsx_path.suffix == file_suffix
        # Sheet_name = None to return OrderedDict of dataframes from each
        # sheet
        df_dict = pd.read_excel(xlsx_path, sheet_name=None)
        return df_dict

    def load_dataframe_from_csv(self, csv_path: str) -> pd.DataFrame:
        csv_path = Path(csv_path)
        file_suffix = ".csv"

        assert csv_path.suffix == file_suffix
        dataframe = pd.read_csv(csv_path)
        return dataframe

    def drop_empty_rows(self,
                        config_dict: t.OrderedDict[str, pd.DataFrame],
                        data_df: pd.DataFrame) -> None:
        raise NotImplementedError


class WaveformDataFrameCleanUp(InputDataFrameCleanup):

    def read_config_update_data(self,
                                config_dict: t.OrderedDict[str, pd.DataFrame],
                                data_df: pd.DataFrame):
        self.rails_to_rename_sheetname(config_dict=config_dict, data_df=data_df)
        self.edge_channels_sheetname(config_dict=config_dict, data_df=data_df)
        self.onboard_rails_sheetname(config_dict=config_dict, data_df=data_df)
        self.timing_sheetname(config_dict=config_dict, data_df=data_df)
        self.sequencing_sheetname(config_dict=config_dict, data_df=data_df)
        self.drop_empty_rows(config_dict=config_dict, data_df=data_df)

    def drop_empty_rows(self,
                        config_dict: t.OrderedDict[str, pd.DataFrame],
                        data_df: pd.DataFrame) -> None:
        drop_subset = ["dut", "pba", "rework", "serial_number", "runid",
                       "scope_channel", "testpoint"]
        data_df.dropna(subset=drop_subset, inplace=True)

    def rails_to_rename_sheetname(self,
                                  config_dict: t.OrderedDict[str, pd.DataFrame],
                                  data_df: pd.DataFrame):
        RAILS_TO_RENAME_SHEETNAME = "Rails to Rename"
        name_rails_df = config_dict.get(RAILS_TO_RENAME_SHEETNAME, None)

        if name_rails_df is None:
            return

        split_names = name_rails_df.to_dict("split")
        '''Split returns :
        {'index': [0, 1, 2], 
        'columns': ['Wrong Name', 'Corrected Name'], 
        'data': [['0P1V_AVDDH', '1P1V_AVDDH'],
                ['test2', 'corrected_2'], 
                ['test3', 'corrected_3']]}
        '''
        for data in split_names['data']:
            wrong_name = data[0]
            right_name = data[1]
            data_df['testpoint'].replace(wrong_name, right_name, inplace=True)
            # If we want to replace the wrong name EVERYWHERE, we can run the
            # below code instead
            # data_file.replace(wrong_name, right_name, inplace=True)

    def edge_channels_sheetname(self,
                                config_dict: t.OrderedDict[str, pd.DataFrame],
                                data_df: pd.DataFrame) -> None:
        EDGE_CHANNEL_SHEETNAME = "Edge Channels"
        edge_df = config_dict.get(EDGE_CHANNEL_SHEETNAME, None)
        if edge_df is None:
            return

        # Create the new columns and fill with default values
        data_df[self.EDGE_RAIL] = False
        data_df[self.ASSOCIATED_EDGE_RAIL] = None
        data_df[self.SPEC_MAX] = np.NaN
        data_df[self.SPEC_MIN] = np.NaN
        data_df[self.EXPECTED_NOMINAL] = np.NaN
        data_df[self.CURRENT_RAIL] = False
        data_df[self.MAX_POWER] = np.NaN

        for i, row in edge_df.iterrows():
            # Update Voltage Rows
            data_df.loc[
                data_df.testpoint == row.Voltage, self.EDGE_RAIL] = True
            data_df.loc[
                data_df.testpoint == row.Voltage,
                self.ASSOCIATED_EDGE_RAIL] = row.Current
            data_df.loc[
                data_df.testpoint == row.Voltage,
                self.EXPECTED_NOMINAL] = row["Nominal Voltage (V)"]
            data_df.loc[
                data_df.testpoint == row.Voltage,
                self.MAX_POWER] = row["Max Power (W)"]

            # Update Current Rows
            data_df.loc[
                data_df.testpoint == row.Current, self.EDGE_RAIL] = True
            data_df.loc[
                data_df.testpoint == row.Current,
                self.ASSOCIATED_EDGE_RAIL] = row.Voltage
            data_df.loc[data_df.testpoint == row.Current,
                        self.SPEC_MAX] = row['Max Current (A)']
            data_df.loc[data_df.testpoint == row.Current,
                        self.CURRENT_RAIL] = True
            data_df.loc[data_df.testpoint == row.Current,
                        self.MAX_POWER] = row['Max Power (W)']

    def onboard_rails_sheetname(self,
                                config_dict: t.OrderedDict[str, pd.DataFrame],
                                data_df: pd.DataFrame) -> None:
        ONBOARD_RAILS_SHEETNAME = "On-Board Rails"
        testpoint_df = config_dict.get(ONBOARD_RAILS_SHEETNAME, None)
        if testpoint_df is None:
            return

        for i, row in testpoint_df.iterrows():
            testpoint = row['Voltage Rail']
            data_df.loc[
                data_df.testpoint == testpoint, self.EXPECTED_NOMINAL] = \
                row['Nominal Value']
            data_df.loc[data_df.testpoint == testpoint, self.SPEC_MIN] = \
                row[
                    'Spec Min']
            data_df.loc[data_df.testpoint == testpoint, self.SPEC_MAX] = \
                row[
                    'Spec Max']

    def sequencing_sheetname(self,
                             config_dict: t.OrderedDict[str, pd.DataFrame],
                             data_df: pd.DataFrame):

        SEQUENCING_SHEETNAME = "Sequencing"
        sequencing_df = config_dict.get(SEQUENCING_SHEETNAME, None)
        if sequencing_df is None:
            return

        # Drop rows with missing values
        # sequencing_df.dropna(axis='index', inplace=True)

        # Reorder Sequencing by Expected Power-on Time
        sequencing_df.sort_values(by="Expected Power-on Time (ms)",
                                  inplace=True)

        # Add appropriate column names to data df
        column_names = {
            "Trace Order": "trace_order",
            "Expected Power-on Time (ms)": "power_on_time_spec",
            "Time Delta (ms)": "time_delta",
            "Valid Voltage (V)": "valid_voltage"
        }
        sequencing_keys = list(column_names.keys())
        data_df_column_names = list(column_names.values())
        data_df[data_df_column_names] = np.NaN

        # Update the datadf with sequencing information from sequencing df
        sequence = 1
        for i, row in sequencing_df.iterrows():
            # Add sequencing and timing information to each
            testpoint = row[sequencing_keys[0]]
            testpoint_indexes = data_df[data_df.testpoint == testpoint].index
            #testpoint_indexes = data_df[data_df.testpoint.str.upper() ==
            #                            testpoint.upper()].index
            data_df.at[testpoint_indexes, data_df_column_names[0]] = sequence

            expected_poweron_time = row[sequencing_keys[1]]
            data_df.at[
                testpoint_indexes, data_df_column_names[
                    1]] = expected_poweron_time

            # time_delta = row[sequencing_keys[2]]
            # data_df.at[
            #    testpoint_indexes, data_df_column_names[2]] =
            #        expected_poweron_time

            # Valid voltage
            # [FLOAT, NONE, or SPEC_MIN] --> All other processing done during
            # test
            valid_voltage = row[sequencing_keys[3]]
            if valid_voltage in ["", None, np.nan]:
                current_rail_bool = data_df[data_df.testpoint == testpoint][
                    "current_rail"].any()
                if current_rail_bool:
                    continue
                valid_voltage = None
            elif isinstance(valid_voltage, str):
                valid_voltage = valid_voltage.lower()
                assert valid_voltage == "spec_min", \
                    f'Sequencing valid voltage must be a number,' \
                    f' empty (current rail) or "spec_min". Not {valid_voltage}.'

            data_df.at[
                testpoint_indexes, data_df_column_names[3]] = valid_voltage

            sequence = sequence + 1

        # Cleanup datatypes
        # data_df[data_df_column_names].astype(dtype=int)

    def timing_sheetname(self, config_dict: t.OrderedDict[str, pd.DataFrame],
                         data_df: pd.DataFrame):

        TIMING_SHEETNAME = "Timing"
        timing_df = config_dict.get(TIMING_SHEETNAME, None)
        if timing_df is None:
            return
        # Drop rows with missing values
        timing_df.dropna(axis='index', inplace=True)

        # Add appropriate column names to data df
        column_names = {
            "From Rail": "testpoint",
            "To Rail": "to_rail",
            "Max Timing (ms)": "to_rail_timing_spec"
        }
        timing_keys = list(column_names.keys())
        data_df_column_names = list(column_names.values())
        # Add columns, but don't add testpoint!
        data_df[data_df_column_names[1:]] = np.NaN

        for i, row in timing_df.iterrows():
            testpoint_indexes = data_df[data_df.testpoint == row[
                timing_keys[0]]].index
            for row_key, timing_key in column_names.items():
                if timing_key == "testpoint":
                    continue
                # Add to_rail to specific testpoint
                data_df.at[testpoint_indexes,
                           timing_key] = row[row_key]


class EthAgentDataFrameCleanup(InputDataFrameCleanup):

    def read_config_update_data(self,
                                config_dict: t.OrderedDict[str, pd.DataFrame],
                                data_df: pd.DataFrame):
        self.ber_sheetname(config_dict=config_dict, data_df=data_df)
        self.drop_empty_rows(config_dict=config_dict, data_df=data_df)

    def drop_empty_rows(self,
                        config_dict: t.OrderedDict[str, pd.DataFrame],
                        data_df: pd.DataFrame) -> None:
        drop_subset = ["dut", "pba", "rework", "serial_number", "runid",
                       "target_confidence"]
        data_df.dropna(subset=drop_subset, inplace=True)

    def ber_sheetname(self, config_dict: t.OrderedDict[str, pd.DataFrame],
                      data_df: pd.DataFrame):
        BER_SHEETNAME = "BER"
        ber_df = config_dict.get(BER_SHEETNAME, None)
        if ber_df is None:
            return
            # Drop rows with missing values
        ber_df.dropna(axis='index', inplace=True)

        # Add appropriate column names to data df
        column_names = {
            "Runid": "runid",
            "Module": "module",
            "BER": "specified_ber",
            "Target Confidence": "target_confidence"
        }
        ber_keys = list(column_names.keys())
        data_df_column_names = list(column_names.values())
        # Add columns, but don't add runid!
        data_df[data_df_column_names[1:]] = np.NaN

        for i, row in ber_df.iterrows():
            runid_indexes = data_df[data_df.runid == row[
                ber_keys[0]]].index
            for row_key, df_key in column_names.items():
                if df_key == "runid":
                    continue
                # Add to_rail to specific testpoint
                data_df.at[runid_indexes, df_key] = row[row_key]


@celeryapp.task(bind=True, base=WaveformDataFrameCleanUp,
                name="waveform_cleanup")
def waveform_cleanup(*args, **kwargs):
    config = kwargs["config_path"]
    data = kwargs["data_path"]
    df_path_str = WaveformDataFrameCleanUp().run(config_path=config,
                                                 data_path=data)
    return df_path_str


@celeryapp.task(bind=True, base=EthAgentDataFrameCleanup,
                name="traffic_cleanup")
def traffic_cleanup(*args, **kwargs):
    config = kwargs["config_path"]
    data = kwargs["data_path"]
    df_path_str = EthAgentDataFrameCleanup().run(config_path=config,
                                                 data_path=data)
    return df_path_str
