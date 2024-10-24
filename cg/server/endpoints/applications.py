from http import HTTPStatus
from typing import Any

from flask import Blueprint, abort, jsonify, make_response, request

from cg.models.orders.constants import OrderType
from cg.server.endpoints.error_handler import handle_missing_entries
from cg.server.endpoints.utils import before_request, is_public
from cg.server.ext import applications_service, db
from cg.services.application.models import ApplicationResponse
from cg.store.models import Application, ApplicationLimitations

APPLICATIONS_BLUEPRINT = Blueprint("applications", __name__, url_prefix="/api/v1")
APPLICATIONS_BLUEPRINT.before_request(before_request)


@APPLICATIONS_BLUEPRINT.route("/applications")
@is_public
def get_applications():
    """Return application tags."""
    applications: list[Application] = db.get_applications_is_not_archived()
    parsed_applications: list[dict] = [application.to_dict() for application in applications]
    return jsonify(applications=parsed_applications)


@APPLICATIONS_BLUEPRINT.route("/applications/order_type")
@handle_missing_entries
def get_application_order_types():
    """Return application order types."""
    order_type = OrderType(request.args.get("order_type"))
    applications: ApplicationResponse = applications_service.get_valid_applications(order_type)
    return jsonify(applications.model_dump())


@APPLICATIONS_BLUEPRINT.route("/applications/<tag>")
@is_public
def get_application(tag: str):
    """Return an application tag."""
    application: Application = db.get_application_by_tag(tag=tag)
    if not application:
        return abort(make_response(jsonify(message="Application not found"), HTTPStatus.NOT_FOUND))

    application_limitations: list[ApplicationLimitations] = db.get_application_limitations_by_tag(
        tag
    )
    application_dict: dict[str, Any] = application.to_dict()
    application_dict["workflow_limitations"] = [
        limitation.to_dict() for limitation in application_limitations
    ]
    return jsonify(**application_dict)


@APPLICATIONS_BLUEPRINT.route("/applications/<tag>/workflow_limitations")
@is_public
def get_application_workflow_limitations(tag: str):
    """Return application workflow specific limitations."""
    if application_limitations := db.get_application_limitations_by_tag(tag):
        return jsonify([limitation.to_dict() for limitation in application_limitations])
    else:
        return jsonify(message="Application limitations not found"), HTTPStatus.NOT_FOUND
