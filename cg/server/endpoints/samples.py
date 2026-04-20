from http import HTTPStatus

from flask import Blueprint, Response, abort, g, jsonify, request
from pydantic import ValidationError

from cg.exc import AuthorisationError, SampleNotFoundError
from cg.server.dto.samples.requests import (
    CollaboratorSamplesRequest,
    SamplesRequest,
    SamplesUpdateRequest,
    UnhandledSamplesRequest,
)
from cg.server.dto.samples.samples_response import SamplesResponse, UnhandledSamplesResponse
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
    return jsonify(**sample.to_dict(links=True))


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
    return jsonify(**sample.to_dict(links=True))


@SAMPLES_BLUEPRINT.route("/samples", methods=["GET"])
def get_samples():
    """Return samples."""
    samples_request = SamplesRequest.model_validate(request.args.to_dict())
    try:
        samples, total = sample_service.get_samples(request=samples_request, user=g.current_user)
    except AuthorisationError:
        return abort(HTTPStatus.FORBIDDEN)
    return jsonify(samples=samples, total=total)


@SAMPLES_BLUEPRINT.route("/unhandled_samples", methods=["GET"])
def get_unhandled_samples():
    try:
        req: UnhandledSamplesRequest = UnhandledSamplesRequest.model_validate(
            request.args.to_dict()
        )
    except ValidationError:
        return abort(code=HTTPStatus.BAD_REQUEST)
    else:
        samples, total = db.get_paginated_unhandled_samples(
            lims_status=req.lims_status, page=req.page, page_size=req.page_size
        )
        response = UnhandledSamplesResponse.from_samples(samples=samples, total=total)
        return jsonify(response.model_dump())


@SAMPLES_BLUEPRINT.route("/samples", methods=["PATCH"])
def update_samples():
    """Update the lims_status attribute of a list of samples."""
    try:
        samples_request = SamplesUpdateRequest.model_validate(request.json)
        for sample in samples_request.samples:
            db.update_sample_lims_status(
                internal_id=sample.internal_id, lims_status=sample.lims_status
            )
    except (SampleNotFoundError, ValidationError):
        return abort(HTTPStatus.BAD_REQUEST)
    db.commit_to_store()
    return Response(status=HTTPStatus.NO_CONTENT)
