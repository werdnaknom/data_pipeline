import typing as t
from io import BytesIO

import pandas as pd


class Formatter:

    def format(self, sheets: t.Dict[str, pd.DataFrame]):
        raise NotImplementedError

    def format_bytesIO(self, sheets: t.Dict[str, pd.DataFrame]) -> BytesIO:
        output = BytesIO()
        formatted_output = self._format(output=output, sheets=sheets)
        formatted_bytes = formatted_output.getvalue()
        return formatted_bytes

    def _format(self, output, sheets: t.Dict[str, pd.DataFrame]):
        return output
