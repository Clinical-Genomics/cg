from http import HTTPStatus
from flask import Blueprint, jsonify, request

from cg.server.dto.samples.collaborator_samples_request import CollaboratorSamplesRequest
from cg.server.dto.samples.samples_response import SamplesResponse
from cg.server.endpoints.utils import before_request
from cg.server.ext import sample_service


SAMPLES_BLUEPRINT = Blueprint("samples", __name__, url_prefix="/api/v1")
SAMPLES_BLUEPRINT.before_request(before_request)


@SAMPLES_BLUEPRINT.route("/samples_in_collaboration")
def get_samples_in_collaboration():
    data = CollaboratorSamplesRequest.model_validate(request.values.to_dict())
    response: SamplesResponse = sample_service.get_collaborator_samples(data)
    return jsonify(response.model_dump()), HTTPStatus.OK
