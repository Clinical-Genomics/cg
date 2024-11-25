from http import HTTPStatus

from flask import Blueprint, abort, g, jsonify, request

from cg.server.dto.samples.requests import CollaboratorSamplesRequest, SamplesRequest
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
    samples_request = SamplesRequest.model_validate(request.args.to_dict())
    if samples_request.status:
        if not g.current_user.is_admin:
            return abort(HTTPStatus.FORBIDDEN)
        else:
            return _get_samples_handled_from_lims(request=samples_request)
    customers: list[Customer] | None = None if g.current_user.is_admin else g.current_user.customers
    samples, total = db.get_samples_by_customers_and_pattern(
        pattern=samples_request.enquiry, customers=customers
    )
    parsed_samples: list[dict] = [sample.to_dict() for sample in samples]
    return jsonify(samples=parsed_samples, total=total)


def _get_samples_handled_from_lims(request: SamplesRequest):
    """Get samples based on the provided status."""
    if request.status == "incoming":
        samples: list[Sample] = db.get_samples_to_receive()
    elif request.status == "labprep":
        samples: list[Sample] = db.get_samples_to_prepare()
    elif request.status == "sequencing":
        samples: list[Sample] = db.get_samples_to_sequence()
    else:
        return abort(HTTPStatus.BAD_REQUEST)
    limit: int = request.page_size or 50
    parsed_samples: list[dict] = [sample.to_dict() for sample in samples[:limit]]
    return jsonify(samples=parsed_samples, total=len(samples))
