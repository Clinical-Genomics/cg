from http import HTTPStatus
from flask import Blueprint, abort, g, jsonify, request

from cg.server.api import BLUEPRINT
from cg.server.dto.samples.collaborator_samples_request import CollaboratorSamplesRequest
from cg.server.dto.samples.samples_response import SamplesResponse
from cg.server.endpoints.utils import before_request
from cg.server.ext import sample_service
from cg.store.models import Customer, Sample

from cg.server.ext import db

SAMPLES_BLUEPRINT = Blueprint("samples", __name__, url_prefix="/api/v1")
SAMPLES_BLUEPRINT.before_request(before_request)


@SAMPLES_BLUEPRINT.route("/samples_in_collaboration")
def get_samples_in_collaboration():
    data = CollaboratorSamplesRequest.model_validate(request.values.to_dict())
    response: SamplesResponse = sample_service.get_collaborator_samples(data)
    return jsonify(response.model_dump()), HTTPStatus.OK


@BLUEPRINT.route("/samples")
def get_samples():
    """Return samples."""
    if request.args.get("status") and not g.current_user.is_admin:
        return abort(HTTPStatus.FORBIDDEN)
    if request.args.get("status") == "incoming":
        samples: list[Sample] = db.get_samples_to_receive()
    elif request.args.get("status") == "labprep":
        samples: list[Sample] = db.get_samples_to_prepare()
    elif request.args.get("status") == "sequencing":
        samples: list[Sample] = db.get_samples_to_sequence()
    else:
        customers: list[Customer] | None = (
            None if g.current_user.is_admin else g.current_user.customers
        )
        samples: list[Sample] = db.get_samples_by_customer_id_and_pattern(
            pattern=request.args.get("enquiry"), customers=customers
        )
    limit = int(request.args.get("limit", 50))
    parsed_samples: list[dict] = [sample.to_dict() for sample in samples[:limit]]
    return jsonify(samples=parsed_samples, total=len(samples))
