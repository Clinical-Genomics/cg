import logging
from http import HTTPStatus

from flask import Blueprint, abort, g, jsonify, request

from cg.exc import CaseNotFoundError, CgDataError, OrderMismatchError
from cg.server.dto.cases.requests import CasesRequest
from cg.server.dto.delivery_message.delivery_message_request import DeliveryMessageRequest
from cg.server.dto.delivery_message.delivery_message_response import DeliveryMessageResponse
from cg.server.endpoints.utils import before_request
from cg.server.ext import case_service, db, delivery_message_service
from cg.store.models import Case, Customer

LOG = logging.getLogger(__name__)
CASES_BLUEPRINT = Blueprint("cases", __name__, url_prefix="/api/v1")
CASES_BLUEPRINT.before_request(before_request)


@CASES_BLUEPRINT.route("/cases")
def get_cases():
    """Return cases with links for a customer from the database."""
    cases_request = CasesRequest.model_validate(request.args.to_dict())

    customers: list[Customer] = _get_current_customers()
    cases, total = case_service.get_cases(request=cases_request, customers=customers)
    return jsonify(cases=cases, total=total)


def _get_current_customers() -> list[Customer] | None:
    """Return customers if the current user is not an admin."""
    return g.current_user.customers if not g.current_user.is_admin else None


@CASES_BLUEPRINT.route("/cases/<case_id>")
def parse_case(case_id):
    """Return a case with links."""
    case: Case = db.get_case_by_internal_id(internal_id=case_id)
    if case is None:
        return abort(HTTPStatus.NOT_FOUND)
    if not g.current_user.is_admin and (case.customer not in g.current_user.customers):
        return abort(HTTPStatus.FORBIDDEN)
    return jsonify(**case.to_dict(links=True, analyses=True))


@CASES_BLUEPRINT.route("/cases/delivery_message", methods=["GET"])
def get_cases_delivery_message():
    delivery_message_request = DeliveryMessageRequest.model_validate(request.args)
    try:
        response: DeliveryMessageResponse = delivery_message_service.get_cases_message(
            delivery_message_request
        )
        return jsonify(response.model_dump()), HTTPStatus.OK
    except (CaseNotFoundError, OrderMismatchError, CgDataError) as error:
        return jsonify({"error": str(error)}), HTTPStatus.BAD_REQUEST


@CASES_BLUEPRINT.route("/cases/<case_id>/delivery_message", methods=["GET"])
def get_case_delivery_message(case_id: str):
    delivery_message_request = DeliveryMessageRequest(case_ids=[case_id])
    try:
        response: DeliveryMessageResponse = delivery_message_service.get_cases_message(
            delivery_message_request
        )
        return jsonify(response.model_dump()), HTTPStatus.OK
    except (CaseNotFoundError, CgDataError) as error:
        return jsonify({"error": str(error)}), HTTPStatus.BAD_REQUEST


@CASES_BLUEPRINT.route("/families_in_collaboration")
def get_cases_in_collaboration():
    """Return cases in collaboration."""

    customer_internal_id = request.args.get("customer")
    workflow = request.args.get("data_analysis")
    case_search_pattern = request.args.get("enquiry")

    customer = db.get_customer_by_internal_id(customer_internal_id=customer_internal_id)

    cases = db.get_cases_by_customer_workflow_and_case_search(
        customer=customer, workflow=workflow, case_search=case_search_pattern
    )

    case_dicts = [case.to_dict(links=True) for case in cases]
    return jsonify(families=case_dicts, total=len(cases))


@CASES_BLUEPRINT.route("/families_in_collaboration/<family_id>")
def get_case_in_collaboration(family_id):
    """Return a case with links."""
    case: Case = db.get_case_by_internal_id(internal_id=family_id)
    customer: Customer = db.get_customer_by_internal_id(
        customer_internal_id=request.args.get("customer")
    )
    if case.customer not in customer.collaborators:
        return abort(HTTPStatus.FORBIDDEN)
    return jsonify(**case.to_dict(links=True, analyses=True))
