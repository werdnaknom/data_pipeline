import typing as t
import logging
import sys
from unittest import TestCase, mock
import datetime
import pickle
from pathlib import Path
from string import ascii_uppercase

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

from basicTestCase.basic_test_case import BasicTestCase
from app.shared.ExcelWriter.excel_formats import FormattingExcelDataFrame

from app.shared.Entities.entities import WaveformEntity
from app.shared.Entities import RunidEntity, WaveformCaptureEntity
from app.shared.Entities._tests.test_helper import dataframe_row


class ExcelFormattingTestCase(BasicTestCase):
    logger_name = "Basic_Excel_Formatting_Tests"
    full_df_paths = Path(
        r"\\npo\coos\LNO_Validation\Improvements\ATS2.0\Andrew's "
        r"Code\unit_test_data\FinalDataFrames")

    def _setUp(self) -> None:
        self.df = pd.read_pickle(self.full_df_paths.joinpath("BER").joinpath(
            'capture_BER_BitErrorRatio.pkl'))

    def test_BER_default_new_class(self):
        path = self.full_df_paths.joinpath("BER")
        xlsx_fmt = FormattingExcelDataFrame(output_path=Path(
            "BER_Default.xlsx"))
        for pkl in path.iterdir():
            df = pd.read_pickle(pkl)
            xlsx_fmt.write_sheet(sheetname=pkl.name[:10], df=df)

        xlsx_fmt.save_excel()

    '''
    def test_simple_output(self):
        # Create a Pandas dataframe from the data.
        df = pd.DataFrame({'Data': [10, 20, 30, 20, 15, 30, 45],
                           'PassFail': ["Pass", "Fail", "Pass", "NA", "Pass",
                                        "NA", "Fail"]})

        # Create a Pandas Excel output_path using XlsxWriter as the engine.
        writer = pd.ExcelWriter('pandas_simple.xlsx', engine='xlsxwriter')

        # Convert the dataframe to an XlsxWriter Excel object.
        df.to_excel(writer, sheet_name='Sheet1')

        # Get the xlsxwriter objects from the dataframe output_path object.
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        excel_formats = ExcelFormats(workbook=workbook)
        excel_formats.conditional_format_passfail(column="C1:C10",
                                                  worksheet=worksheet)
        # Sets horizontal size of column
        worksheet.set_column(0, 0, 30)

        worksheet.set_column("B:B", 10, excel_formats.temperature_format)
        # Filter
        worksheet.autofilter('A1:D51')

        # Freeze Panes
        worksheet.freeze_panes(1, 0)

        # Add Comment to Cell
        # worksheet.write_comment('C1', 'Always Visible comment',
        #                        {"visible": True})
        worksheet.write_comment('B1', 'Scroll over cell to see comment')

        # Worksheet set the color of the tab
        worksheet.set_tab_color("red")

        # Create a chart object.
        chart = workbook.add_chart({'type': 'column'})

        # Configure the series of the chart from the dataframe data.
        chart.add_series({'values': '=Sheet1!$B$2:$B$8'})

        # Insert the chart into the worksheet.
        worksheet.insert_chart('D2', chart)

        # Apply a conditional format to the cell range.
        worksheet.conditional_format('B2:B8', {'type': '3_color_scale'})

        # Add a header format.
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1})

        # Write the column headers with the defined format.
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num + 1, value, header_format)

        # Close the Pandas Excel output_path and output the Excel file.
        writer.save()
    '''
