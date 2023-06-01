from flask import jsonify, request, make_response
from io import BytesIO

from Processing.TestDataPipelines import SequencingDataProcessingPipeline, OverviewDataProcessingPipeline
from ResultFormatting.excel_formatter import OpenpyxlFormatter, XLSXFormatter

from . import bp


@bp.route('/sequencing_pipeline', methods=["POST", "GET"])
def sequencing():
    pipeline = SequencingDataProcessingPipeline()
    json_request = {"product": "Clara Peak",
                    "runid_status": ["Complete"],
                    # "test_category_list": ["Off to Aux and Main"],
                    "runid_list": [6799]
                    }

    sheets = pipeline.process_data(json_request=json_request)
    formatter = XLSXFormatter()
    excel_bytes: BytesIO = formatter.format_bytesIO(sheets=sheets)

    response = make_response(excel_bytes)
    response.headers.set('Content-Disposition', 'attachment',
                         filename=f'test.xlsx')
    return response


@bp.route('/overview_pipeline', methods=["POST", "GET"])
def overview():
    pipeline = OverviewDataProcessingPipeline()
    json_request = {"product": "Clara Peak",
                    "runid_status": ["Complete"],
                    "test_category_list": ["Off to Aux and Main"],
                    "runid_list": [6799]
                    }

    sheets = pipeline.process_data(json_request=json_request)
    formatter = XLSXFormatter()
    excel_bytes: BytesIO = formatter.format_bytesIO(sheets=sheets)

    response = make_response(excel_bytes)
    response.headers.set('Content-Disposition', 'attachment',
                         filename=f'test.xlsx')
    return response
