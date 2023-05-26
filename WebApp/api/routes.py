import json
import typing as t
from dataclasses import asdict, dataclass

from flask import jsonify, request, make_response
#from Processing.usecase import WaveformReviewer, TestpointInfo

from Processing.WaveformProcessing.waveform_processing_usecase import WaveformProcessingUseCase
from Entities.WaveformFunctions.waveform_analysis import WaveformAnalysis

from . import bp


@bp.route("/runid_directory_add_waveforms", methods=["POST"])
def from_runid_directory_add_waveforms():
    return wfm_list

@bp.route('/waveform-review-excel', methods=['GET'])
def json_to_excel():
    return response
