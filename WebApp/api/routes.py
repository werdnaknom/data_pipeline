from flask import jsonify, request, make_response
from io import BytesIO

from Processing.TestDataPipelines.sequencing_pipeline import SequencingDataProcessingPipeline
from ResultFormatting.excel_formatter import OpenpyxlFormatter, XLSXFormatter

from . import bp


@bp.route('/sequencing_pipeline', methods=["POST","GET"])
def sequencing():
    pipeline = SequencingDataProcessingPipeline()
    sheets = pipeline.process_data()
    formatter = XLSXFormatter()
    excel_bytes: BytesIO = formatter.format_bytesIO(sheets=sheets)

    response = make_response(excel_bytes)
    response.headers.set('Content-Disposition', 'attachment',
                         filename=f'test.xlsx')
    return response
