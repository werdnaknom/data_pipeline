from flask import jsonify, request, make_response

from Processing.TestDataPipelines.sequencing_pipeline import SequencingDataProcessingPipeline

from . import bp


@bp.route('/sequencing_pipeline', methods=["POST"])
def sequencing():
    pipeline = SequencingDataProcessingPipeline()
    pipeline.process_data()
