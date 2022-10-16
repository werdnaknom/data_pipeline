import typing as t

from pathlib import Path
import xlsxwriter as xlsx

import pandas as pd
import numpy as np

# Intel Blue
HEADERFORMAT = {'bg_color': '#007DC3',
                'text_wrap': True,
                'valign': 'top',
                'border': 1,
                'bold': True}
# Nintendo Logo colors
FAILFORMAT = {'bg_color': '#E60012',  # '#FFC7CE',
              'font_color': '#FFFFFF',  # '#9C0006',
              'bold': True,
              'border': True}
PASSFORMAT = {'bg_color': '#00B287',  # '#C6EFCE',
              'font_color': '#FFFFFF',  # '#006100',
              'bold': True}
NAFORMAT = {'bg_color': '#A5A5A5',
            'font_color': '#FFFFFF',
            'bold': True}
# Yahoo Logo Colors
REVIEWEDFORMAT = {'bg_color': '#720E9E',
                  'font_color': '#FFFFFF',
                  'bold': True}
HYPERLINKFORMAT = {'font_color': 'blue',
                   'underline': True}
VOLTAGEFORMAT = {'num_format': '#,##0.00 V'}
MILLIVOLTAGEFORMAT = {'num_format': '#,##0.00 mV'}
AMPFORMAT = {'num_format': '#,##0.00 A'}
MILLIAMPFORMAT = {'num_format': '#,##0.00 mA'}
POWERFORMAT = {'num_format': '#,##0.00W'}
TEMPERATUREFORMAT = {'num_format': u'#,##0.0\N{DEGREE SIGN}C'}

ZEBRA_COLOR1 = {"bg_color": "#EAEAEA"}
ZEBRA_COLOR2 = {"bg_color": "#F8F8F8"}
SIDEBORDER = {'left': 1,
              'right': 1}


class FormattingExcelDataFrame():

    def __init__(self, output_path: Path, test_specific_headers: list = None):
        assert output_path.suffix == ".xlsx", \
            f"{output_path} must have suffix .xlsx"
        if not test_specific_headers:
            test_specific_headers = []
        assert isinstance(test_specific_headers, list), \
            f"{test_specific_headers} must be a list!"
        self.test_specific_headers = test_specific_headers

        xlsx_file = output_path.with_suffix(".xlsx")
        self.output_path = xlsx_file
        self.writer = pd.ExcelWriter(path=self.output_path,
                                     engine='xlsxwriter')
        self._create_formats()

    '''
    def _wrte_sheet(self, sheetname: str, df: pd.DataFrame):
        worksheet = self.writer.book.add_worksheet(name=sheetname)
        header_row, last_row, first_col, last_col = self.get_table_size(df=df,
                                                                        index=False)
        worksheet.add_table(first_row=header_row, first_col=first_col,
                            last_row=last_row, last_col=last_col,
                            options={
                                
                            })
    '''

    def write_sheet(self, sheetname: str, df: pd.DataFrame):
        index = False
        df.to_excel(excel_writer=self.writer, sheet_name=sheetname, index=index)
        worksheet = self.writer.sheets[sheetname]
        header_row, lastrow, first_col, last_col = self.get_table_size(df=df,
                                                                       index=index)
        # self._add_zebra(worksheet=worksheet, last_row=lastrow,
        #                header=header_row)
        self._format_cells(worksheet=worksheet, df=df, index=False)
        self._add_table(worksheet=worksheet, df=df, index=False)
        # self._worksheet_autofilter(worksheet=worksheet, df=df)

    def _format_columns(self, df) -> t.List[dict]:
        column_list = []
        for header in df.columns.values:
            header_dict = {"header": header,
                           "header_format": self.header_format}
            column_list.append(header_dict)
        return column_list

    def _add_table(self, worksheet, df: pd.DataFrame, index: bool = False):
        header_row, last_row, first_col, last_col = \
            self.get_table_size(df=df, index=index)
        table_options = {
            'style': 'Table Style Light 1',
            'header_row': True,
            'columns': self._format_columns(df=df)
        }
        worksheet.add_table(first_row=header_row, last_row=last_row,
                            first_col=first_col, last_col=last_col,
                            options=table_options)

    def _create_formats(self):
        self.zebra1_format = self.writer.book.add_format(
            properties=ZEBRA_COLOR1)
        self.zebra2_format = self.writer.book.add_format(
            properties=ZEBRA_COLOR2)
        self.header_format = self.writer.book.add_format(
            properties=HEADERFORMAT)
        self.pass_format = self.writer.book.add_format(
            properties=PASSFORMAT)
        self.fail_format = self.writer.book.add_format(
            properties=FAILFORMAT)
        self.na_format = self.writer.book.add_format(
            properties=NAFORMAT)
        self.review_format = self.writer.book.add_format(
            properties=REVIEWEDFORMAT)
        self.voltage_format = self.writer.book.add_format(
            properties=VOLTAGEFORMAT)
        self.current_format = self.writer.book.add_format(
            properties=AMPFORMAT)
        self.power_format = self.writer.book.add_format(
            properties=POWERFORMAT)
        self.temperature_format = self.writer.book.add_format(
            properties=TEMPERATUREFORMAT)
        self.hyperlink_format = self.writer.book.add_format(
            properties=HYPERLINKFORMAT)
        self.side_border_format = self.writer.book.add_format(
            properties=SIDEBORDER)
        self._testspecific_formats()

    def _testspecific_formats(self):
        ''' Not always implemented '''
        pass

    def _testspecific_formatting(self, worksheet, column: int, first_row: int,
                                 last_row: int, value: str):
        ''' Not always implemented '''
        # Value == Column header
        pass

    @classmethod
    def _calculate_column_width(cls, column: np.ndarray, header: str) -> int:
        # Split the header into individual words
        # Take the length of the longest word
        header_length = len(max(header.split(" "), key=len))
        # Convert the column data into a string
        # Take the length of the longest data element
        data_length = len(max(column.astype(str), key=len))

        final_max = max([data_length, header_length]) + 5  # generic adder
        return final_max

    def _write_header(self, worksheet, column: int, value: str,
                      header: int = 0):
        '''Writes Header'''
        worksheet.write(header, column, value, self.header_format)

    def _format_cells(self, worksheet, df: pd.DataFrame, index: bool = False):
        header, last_row, first_col, last_col = self.get_table_size(df=df,
                                                                    index=index)
        first_row = header + 1
        for col_num, value in enumerate(df.columns.values):
            self._write_header(worksheet=worksheet, header=header,
                               column=col_num, value=value)

            if index:
                col_num = col_num + 1

            column_width = self._calculate_column_width(column=df[value],
                                                        header=value)
            if value == "Temperature (C)":
                # Format Temperature Column
                worksheet.set_column(first_col=col_num, last_col=col_num,
                                     width=column_width,
                                     cell_format=self.temperature_format)

            elif "(V)" in value:
                # Format Voltage Columns
                worksheet.set_column(first_col=col_num, last_col=col_num,
                                     width=column_width,
                                     cell_format=self.voltage_format)
            elif "(A)" in value:
                # Format Voltage Columns
                worksheet.set_column(first_col=col_num, last_col=col_num,
                                     width=column_width,
                                     cell_format=self.current_format)
            elif "(W)" in value:
                # Format Voltage Columns
                worksheet.set_column(first_col=col_num, last_col=col_num,
                                     width=column_width,
                                     cell_format=self.power_format)
            elif value == "Result":
                # Format Result Columns
                self.conditional_format_passfail(worksheet=worksheet,
                                                 column=col_num,
                                                 last_row=last_row,
                                                 first_row=first_row)
            elif "Plot" in value or "Image" in value:
                # Format plot as hyperlink
                # Override column width because it is calculated on the full
                # =HYPERLINK(...) text
                column_width = len(value) + 5
                worksheet.set_column(first_col=col_num, last_col=col_num,
                                     width=column_width,
                                     cell_format=self.hyperlink_format)
            elif "Histogram" in value:
                # Format plot as hyperlink
                # Override column width because it is calculated on the full
                # =HYPERLINK(...) text
                column_width = len(value) + 5
                worksheet.set_column(first_col=col_num, last_col=col_num,
                                     width=column_width,
                                     cell_format=self.hyperlink_format)
            elif value in self.test_specific_headers:
                self._testspecific_formatting(worksheet=worksheet, value=value,
                                              column=col_num, last_row=last_row,
                                              first_row=first_row)
            else:
                # Format undefined Columns
                worksheet.set_column(first_col=col_num, last_col=col_num,
                                     width=column_width)

    def get_table_size(self, df: pd.DataFrame, index: bool = False) -> \
            t.Tuple[int, int, int, int]:
        rows, cols = df.shape
        header_row = 0
        last_row = rows
        if index:
            first_col = 1
            last_col = cols
        else:
            first_col = 0
            last_col = cols - 1

        return header_row, last_row, first_col, last_col

    def ber_error_failure(self, column: str, worksheet):
        worksheet.conditional_format(column,
                                     {"type": 'cell',
                                      "criteria": ">",
                                      'value': 0,
                                      'format': {"font_color": "red"}}
                                     )

    def conditional_format_passfail(self, worksheet, column: int,
                                    last_row: int, first_row: int = 1):
        worksheet.conditional_format(first_row=first_row, first_col=column,
                                     last_row=last_row, last_col=column,
                                     options={'type': 'cell',
                                              'criteria': 'equal',
                                              'value': '"Pass"',
                                              'format': self.pass_format})
        worksheet.conditional_format(first_row, column, last_row, column,
                                     {'type': 'cell',
                                      'criteria': 'equal',
                                      'value': '"Fail"',
                                      'format': self.fail_format})
        worksheet.conditional_format(first_row, column, last_row, column,
                                     {'type': 'cell',
                                      'criteria': 'equal',
                                      'value': '"N/A"',
                                      'format': self.na_format})
        worksheet.conditional_format(first_row, column, last_row, column,
                                     {'type': 'cell',
                                      'criteria': 'equal',
                                      'value': '"Reviewed"',
                                      'format': self.review_format})

    def save_excel(self):
        '''
        This saves the excel file and makes it accessible by other users.
        @return:
        '''
        self.writer.save()
