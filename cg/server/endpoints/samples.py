from http import HTTPStatus

from flask import Blueprint, abort, g, jsonify, request

from cg.server.dto.samples.collaborator_samples_request import (
    CollaboratorSamplesRequest,
)
from cg.server.dto.samples.samples_response import SamplesResponse
from cg.server.endpoints.utils import before_request
from cg.server.ext import db, sample_service
from cg.store.models import Customer, Sample

SAMPLES_BLUEPRINT = Blueprint("samples", __name__, url_prefix="/api/v1")
SAMPLES_BLUEPRINT.before_request(before_request)


@SAMPLES_BLUEPRINT.route("/samples/<sample_id>")
def get_sample(sample_id):
    sample: Sample | None = db.get_sample_by_internal_id(sample_id)
    if sample is None:
        return abort(HTTPStatus.NOT_FOUND)
    if not g.current_user.is_admin and (sample.customer not in g.current_user.customers):
        return abort(HTTPStatus.FORBIDDEN)
    return jsonify(**sample.to_dict(links=True, flowcells=True))


@SAMPLES_BLUEPRINT.route("/samples_in_collaboration")
def get_samples_in_collaboration():
    data = CollaboratorSamplesRequest.model_validate(request.values.to_dict())
    response: SamplesResponse = sample_service.get_collaborator_samples(data)
    return jsonify(response.model_dump()), HTTPStatus.OK


@SAMPLES_BLUEPRINT.route("/samples_in_collaboration/<sample_id>")
def parse_sample_in_collaboration(sample_id):
    """Return a single sample."""
    sample: Sample = db.get_sample_by_internal_id(sample_id)
    customer: Customer = db.get_customer_by_internal_id(
        customer_internal_id=request.args.get("customer")
    )
    if sample.customer not in customer.collaborators:
        return abort(HTTPStatus.FORBIDDEN)
    return jsonify(**sample.to_dict(links=True, flowcells=True))


@SAMPLES_BLUEPRINT.route("/samples")
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
        samples: list[Sample] = db.get_samples_by_customers_and_pattern(
            pattern=request.args.get("enquiry"), customers=customers
        )
    limit = int(request.args.get("limit", 50))
    parsed_samples: list[dict] = [sample.to_dict() for sample in samples[:limit]]
    return jsonify(samples=parsed_samples, total=len(samples))
