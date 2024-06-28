import json
import logging
import tempfile
from functools import wraps
from http import HTTPStatus
from pathlib import Path
from typing import Any

import cachecontrol
import requests
from flask import Blueprint, abort, current_app, g, jsonify, make_response, request
from google.auth import exceptions
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic.v1 import ValidationError
from requests.exceptions import HTTPError
from sqlalchemy.exc import IntegrityError
from urllib3.exceptions import MaxRetryError, NewConnectionError
from werkzeug.utils import secure_filename

from cg.apps.orderform.excel_orderform_parser import ExcelOrderformParser
from cg.apps.orderform.json_orderform_parser import JsonOrderformParser
from cg.constants import ANALYSIS_SOURCES, METAGENOME_SOURCES
from cg.constants.constants import FileFormat
from cg.exc import (
    CaseNotFoundError,
    OrderError,
    OrderExistsError,
    OrderFormError,
    OrderMismatchError,
    OrderNotDeliverableError,
    OrderNotFoundError,
    TicketCreationError,
)
from cg.io.controller import WriteStream
from cg.meta.orders import OrdersAPI
from cg.meta.orders.ticket_handler import TicketHandler
from cg.models.orders.order import OrderIn, OrderType
from cg.models.orders.orderform_schema import Orderform
from cg.server.dto.delivery_message.delivery_message_request import (
    DeliveryMessageRequest,
)
from cg.server.dto.delivery_message.delivery_message_response import (
    DeliveryMessageResponse,
)
from cg.server.dto.orders.order_delivery_update_request import OrderDeliveredUpdateRequest
from cg.server.dto.orders.order_patch_request import OrderDeliveredPatch
from cg.server.dto.orders.orders_request import OrdersRequest
from cg.server.dto.orders.orders_response import Order, OrdersResponse
from cg.server.dto.sequencing_metrics.sequencing_metrics_request import SequencingMetricsRequest
from cg.server.ext import db, delivery_message_service, lims, order_service, osticket
from cg.store.models import (
    Analysis,
    Application,
    Case,
    Customer,
    Flowcell,
    Pool,
    Sample,
    SampleLaneSequencingMetrics,
    User,
    ApplicationLimitations,
)

LOG = logging.getLogger(__name__)
BLUEPRINT = Blueprint("api", __name__, url_prefix="/api/v1")


session = requests.session()
cached_session = cachecontrol.CacheControl(session)


def verify_google_token(token):
    request = google_requests.Request(session=cached_session)
    return id_token.verify_oauth2_token(id_token=token, request=request)


def is_public(route_function):
    @wraps(route_function)
    def public_endpoint(*args, **kwargs):
        return route_function(*args, **kwargs)

    public_endpoint.is_public = True
    return public_endpoint


@BLUEPRINT.before_request
def before_request():
    """Authorize API routes with JSON Web Tokens."""
    if not request.is_secure:
        return abort(
            make_response(jsonify(message="Only https requests accepted"), HTTPStatus.FORBIDDEN)
        )

    if request.method == "OPTIONS":
        return make_response(jsonify(ok=True), HTTPStatus.NO_CONTENT)

    endpoint_func = current_app.view_functions[request.endpoint]
    if getattr(endpoint_func, "is_public", None):
        return

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return abort(
            make_response(jsonify(message="no JWT token found on request"), HTTPStatus.UNAUTHORIZED)
        )

    jwt_token = auth_header.split("Bearer ")[-1]
    try:
        user_data = verify_google_token(jwt_token)
    except (exceptions.OAuthError, ValueError) as e:
        LOG.error(f"Error {e} occurred while decoding JWT token: {jwt_token}")
        return abort(
            make_response(jsonify(message="outdated login certificate"), HTTPStatus.UNAUTHORIZED)
        )

    user: User = db.get_user_by_email(user_data["email"])
    if user is None or not user.order_portal_login:
        message = f"{user_data['email']} doesn't have access"
        LOG.error(message)
        return abort(make_response(jsonify(message=message), HTTPStatus.FORBIDDEN))

    g.current_user = user


@BLUEPRINT.route("/submit_order/<order_type>", methods=["POST"])
def submit_order(order_type):
    """Submit an order for samples."""
    api = OrdersAPI(lims=lims, status=db, osticket=osticket)
    error_message: str
    try:
        request_json = request.get_json()
        LOG.info(
            "processing order: %s",
            WriteStream.write_stream_from_content(
                content=request_json, file_format=FileFormat.JSON
            ),
        )
        project = OrderType(order_type)
        order_in = OrderIn.parse_obj(request_json, project=project)
        existing_ticket: str | None = TicketHandler.parse_ticket_number(order_in.name)
        if existing_ticket and order_service.store.get_order_by_ticket_id(existing_ticket):
            raise OrderExistsError(f"Order with ticket id {existing_ticket} already exists.")

        result: dict = api.submit(
            project=project,
            order_in=order_in,
            user_name=g.current_user.name,
            user_mail=g.current_user.email,
        )
        order_service.create_order(order_in)

    except (  # user misbehaviour
        OrderError,
        OrderExistsError,
        OrderFormError,
        ValidationError,
        ValueError,
    ) as error:
        error_message = error.message if hasattr(error, "message") else str(error)
        http_error_response = HTTPStatus.BAD_REQUEST
        LOG.error(error_message)
    except (  # system misbehaviour
        AttributeError,
        ConnectionError,
        HTTPError,
        IntegrityError,
        KeyError,
        NewConnectionError,
        MaxRetryError,
        TimeoutError,
        TicketCreationError,
        TypeError,
    ) as error:
        LOG.exception(error)
        error_message = error.message if hasattr(error, "message") else str(error)
        http_error_response = HTTPStatus.INTERNAL_SERVER_ERROR
    else:
        return jsonify(
            project=result["project"], records=[record.to_dict() for record in result["records"]]
        )

    if error_message:
        return abort(make_response(jsonify(message=error_message), http_error_response))


@BLUEPRINT.route("/cases")
def get_cases():
    """Return cases with links for a customer from the database."""
    enquiry: str = request.args.get("enquiry")
    action: str = request.args.get("action")

    customers: list[Customer] = _get_current_customers()
    cases: list[Case] = _get_cases(enquiry=enquiry, action=action, customers=customers)

    nr_cases: int = len(cases)
    cases_with_links: list[dict] = [case.to_dict(links=True) for case in cases]
    return jsonify(families=cases_with_links, total=nr_cases)


def _get_current_customers() -> list[Customer] | None:
    """Return customers if the current user is not an admin."""
    return g.current_user.customers if not g.current_user.is_admin else None


def _get_cases(
    enquiry: str | None, action: str | None, customers: list[Customer] | None
) -> list[Case]:
    """Get cases based on the provided filters."""
    return db.get_cases_by_customers_action_and_case_search(
        case_search=enquiry,
        customers=customers,
        action=action,
    )


@BLUEPRINT.route("/cases/<case_id>")
def parse_case(case_id):
    """Return a case with links."""
    case: Case = db.get_case_by_internal_id(internal_id=case_id)
    if case is None:
        return abort(HTTPStatus.NOT_FOUND)
    if not g.current_user.is_admin and (case.customer not in g.current_user.customers):
        return abort(HTTPStatus.FORBIDDEN)
    return jsonify(**case.to_dict(links=True, analyses=True))


@BLUEPRINT.route("/cases/delivery_message", methods=["GET"])
def get_cases_delivery_message():
    delivery_message_request = DeliveryMessageRequest.model_validate(request.args)
    try:
        response: DeliveryMessageResponse = delivery_message_service.get_cases_message(
            delivery_message_request
        )
        return jsonify(response.model_dump()), HTTPStatus.OK
    except (CaseNotFoundError, OrderMismatchError) as error:
        return jsonify({"error": str(error)}), HTTPStatus.BAD_REQUEST


@BLUEPRINT.route("/cases/<case_id>/delivery_message", methods=["GET"])
def get_case_delivery_message(case_id: str):
    delivery_message_request = DeliveryMessageRequest(case_ids=[case_id])
    try:
        response: DeliveryMessageResponse = delivery_message_service.get_cases_message(
            delivery_message_request
        )
        return jsonify(response.model_dump()), HTTPStatus.OK
    except CaseNotFoundError as error:
        return jsonify({"error": str(error)}), HTTPStatus.BAD_REQUEST


@BLUEPRINT.route("/families_in_collaboration")
def parse_families_in_collaboration():
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


@BLUEPRINT.route("/families_in_collaboration/<family_id>")
def parse_family_in_collaboration(family_id):
    """Return a family with links."""
    case: Case = db.get_case_by_internal_id(internal_id=family_id)
    customer: Customer = db.get_customer_by_internal_id(
        customer_internal_id=request.args.get("customer")
    )
    if case.customer not in customer.collaborators:
        return abort(HTTPStatus.FORBIDDEN)
    return jsonify(**case.to_dict(links=True, analyses=True))


@BLUEPRINT.route("/samples")
def parse_samples():
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


@BLUEPRINT.route("/samples_in_collaboration")
def parse_samples_in_collaboration():
    """Return samples in a customer group."""
    customer: Customer = db.get_customer_by_internal_id(
        customer_internal_id=request.args.get("customer")
    )
    samples: list[Sample] = db.get_samples_by_customer_id_and_pattern(
        pattern=request.args.get("enquiry"), customers=customer.collaborators
    )
    limit = int(request.args.get("limit", 50))
    parsed_samples: list[dict] = [sample.to_dict() for sample in samples[:limit]]
    return jsonify(samples=parsed_samples, total=len(samples))


@BLUEPRINT.route("/samples/<sample_id>")
def parse_sample(sample_id):
    """Return a single sample."""
    sample: Sample = db.get_sample_by_internal_id(sample_id)
    if sample is None:
        return abort(HTTPStatus.NOT_FOUND)
    if not g.current_user.is_admin and (sample.customer not in g.current_user.customers):
        return abort(HTTPStatus.FORBIDDEN)
    return jsonify(**sample.to_dict(links=True, flowcells=True))


@BLUEPRINT.route("/samples_in_collaboration/<sample_id>")
def parse_sample_in_collaboration(sample_id):
    """Return a single sample."""
    sample: Sample = db.get_sample_by_internal_id(sample_id)
    customer: Customer = db.get_customer_by_internal_id(
        customer_internal_id=request.args.get("customer")
    )
    if sample.customer not in customer.collaborators:
        return abort(HTTPStatus.FORBIDDEN)
    return jsonify(**sample.to_dict(links=True, flowcells=True))


@BLUEPRINT.route("/pools")
def parse_pools():
    """Return pools."""
    customers: list[Customer] | None = (
        g.current_user.customers if not g.current_user.is_admin else None
    )
    pools: list[Pool] = db.get_pools_to_render(
        customers=customers, enquiry=request.args.get("enquiry")
    )
    parsed_pools: list[dict] = [pool_obj.to_dict() for pool_obj in pools[:30]]
    return jsonify(pools=parsed_pools, total=len(pools))


@BLUEPRINT.route("/pools/<pool_id>")
def parse_pool(pool_id):
    """Return a single pool."""
    pool: Pool = db.get_pool_by_entry_id(entry_id=pool_id)
    if pool is None:
        return abort(HTTPStatus.NOT_FOUND)
    if not g.current_user.is_admin and (pool.customer not in g.current_user.customers):
        return abort(HTTPStatus.FORBIDDEN)
    return jsonify(**pool.to_dict())


@BLUEPRINT.route("/flowcells")
def parse_flow_cells() -> Any:
    """Return flow cells."""
    flow_cells: list[Flowcell] = db.get_flow_cell_by_name_pattern_and_status(
        flow_cell_statuses=[request.args.get("status")],
        name_pattern=request.args.get("enquiry"),
    )
    parsed_flow_cells: list[dict] = [flow_cell.to_dict() for flow_cell in flow_cells[:50]]
    return jsonify(flowcells=parsed_flow_cells, total=len(flow_cells))


@BLUEPRINT.route("/flowcells/<flowcell_id>")
def parse_flow_cell(flowcell_id):
    """Return a single flowcell."""
    flow_cell: Flowcell = db.get_flow_cell_by_name(flow_cell_name=flowcell_id)
    if flow_cell is None:
        return abort(HTTPStatus.NOT_FOUND)
    return jsonify(**flow_cell.to_dict(samples=True))


@BLUEPRINT.route("/flowcells/<flow_cell_name>/sequencing_metrics", methods=["GET"])
def get_sequencing_metrics(flow_cell_name: str):
    """Return sample lane sequencing metrics for a flow cell."""
    if not flow_cell_name:
        return jsonify({"error": "Invalid or missing flow cell id"}), HTTPStatus.BAD_REQUEST
    sequencing_metrics: list[SampleLaneSequencingMetrics] = (
        db.get_sample_lane_sequencing_metrics_by_flow_cell_name(flow_cell_name)
    )
    if not sequencing_metrics:
        return (
            jsonify({"error": f"Sequencing metrics not found for flow cell {flow_cell_name}."}),
            HTTPStatus.NOT_FOUND,
        )
    metrics_dtos: list[SequencingMetricsRequest] = [
        SequencingMetricsRequest.model_validate(metric, from_attributes=True)
        for metric in sequencing_metrics
    ]
    return jsonify([metric.model_dump() for metric in metrics_dtos])


@BLUEPRINT.route("/analyses")
def parse_analyses():
    """Return analyses."""
    if request.args.get("status") == "delivery":
        analyses: list[Analysis] = db.get_analyses_to_deliver_for_pipeline()
    elif request.args.get("status") == "upload":
        analyses: list[Analysis] = db.get_analyses_to_upload()
    else:
        analyses: list[Analysis] = db.get_analyses()
    parsed_analysis: list[dict] = [analysis_obj.to_dict() for analysis_obj in analyses[:30]]
    return jsonify(analyses=parsed_analysis, total=len(analyses))


@BLUEPRINT.route("/options")
def parse_options():
    """Return various options."""
    customers: list[Customer | None] = (
        db.get_customers() if g.current_user.is_admin else g.current_user.customers
    )

    app_tag_groups: dict[str, list[str]] = {"ext": []}
    applications: list[Application] = db.get_applications_is_not_archived()
    for application in applications:
        if not application.versions:
            LOG.debug(f"Skipping application {application} that doesn't have a price")
            continue
        if application.is_external:
            app_tag_groups["ext"].append(application.tag)
        if application.prep_category not in app_tag_groups:
            app_tag_groups[application.prep_category]: list[str] = []
        app_tag_groups[application.prep_category].append(application.tag)

    source_groups = {"metagenome": METAGENOME_SOURCES, "analysis": ANALYSIS_SOURCES}

    return jsonify(
        applications=app_tag_groups,
        beds=[bed.name for bed in db.get_active_beds()],
        customers=[
            {
                "text": f"{customer.name} ({customer.internal_id})",
                "value": customer.internal_id,
                "isTrusted": customer.is_trusted,
            }
            for customer in customers
        ],
        organisms=[
            {
                "name": organism.name,
                "reference_genome": organism.reference_genome,
                "internal_id": organism.internal_id,
                "verified": organism.verified,
            }
            for organism in db.get_all_organisms()
        ],
        panels=[panel.abbrev for panel in db.get_panels()],
        sources=source_groups,
    )


@BLUEPRINT.route("/me")
def parse_current_user_information():
    """Return information about current user."""
    if not g.current_user.is_admin and not g.current_user.customers:
        LOG.error(
            "%s is not admin and is not connected to any customers, aborting", g.current_user.email
        )
        return abort(HTTPStatus.FORBIDDEN)

    return jsonify(user=g.current_user.to_dict())


@BLUEPRINT.route("/applications")
@is_public
def parse_applications():
    """Return application tags."""
    applications: list[Application] = db.get_applications_is_not_archived()
    parsed_applications: list[dict] = [application.to_dict() for application in applications]
    return jsonify(applications=parsed_applications)


@BLUEPRINT.route("/applications/<tag>")
@is_public
def parse_application(tag: str):
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


@BLUEPRINT.route("/applications/<tag>/workflow_limitations")
@is_public
def get_application_workflow_limitations(tag: str):
    """Return application workflow specific limitations."""
    if application_limitations := db.get_application_limitations_by_tag(tag):
        return jsonify([limitation.to_dict() for limitation in application_limitations])
    else:
        return jsonify(message="Application limitations not found"), HTTPStatus.NOT_FOUND


@BLUEPRINT.route("/orders")
def get_orders():
    """Return the latest orders."""
    data = OrdersRequest.model_validate(request.args.to_dict())
    response: OrdersResponse = order_service.get_orders(data)
    return make_response(response.model_dump())


@BLUEPRINT.route("/orders/<order_id>")
def get_order(order_id: int):
    """Return an order."""
    try:
        response: Order = order_service.get_order(order_id)
        response_dict: dict = response.model_dump()
        return make_response(response_dict)
    except OrderNotFoundError as error:
        return make_response(jsonify(error=str(error)), HTTPStatus.NOT_FOUND)


@BLUEPRINT.route("/orders/<order_id>/delivered", methods=["PATCH"])
def set_order_delivered(order_id: int):
    try:
        request_data = OrderDeliveredPatch.model_validate(request.json)
        delivered: bool = request_data.delivered
        response_data: Order = order_service.set_delivery(order_id=order_id, delivered=delivered)
        return jsonify(response_data.model_dump()), HTTPStatus.OK
    except OrderNotFoundError as error:
        return jsonify(error=str(error)), HTTPStatus.NOT_FOUND


@BLUEPRINT.route("/orders/<order_id>/update-delivery-status", methods=["POST"])
def update_order_delivered(order_id: int):
    """Update the delivery status of an order based on the number of delivered analyses."""
    try:
        request_data = OrderDeliveredUpdateRequest.model_validate(request.json)
        delivered_analyses: int = request_data.delivered_analyses_count
        order_service.update_delivered(order_id=order_id, delivered_analyses=delivered_analyses)
    except OrderNotFoundError as error:
        return jsonify(error=str(error)), HTTPStatus.NOT_FOUND


@BLUEPRINT.route("/orders/<order_id>/delivery_message")
def get_delivery_message_for_order(order_id: int):
    """Return the delivery message for an order."""
    try:
        response: DeliveryMessageResponse = delivery_message_service.get_order_message(order_id)
        response_dict: dict = response.model_dump()
        return make_response(response_dict)
    except OrderNotDeliverableError as error:
        return make_response(jsonify(error=str(error)), HTTPStatus.PRECONDITION_FAILED)
    except OrderNotFoundError as error:
        return make_response(jsonify(error=str(error))), HTTPStatus.NOT_FOUND


@BLUEPRINT.route("/orderform", methods=["POST"])
def parse_orderform():
    """Parse an orderform/JSON export."""
    input_file = request.files.get("file")
    filename = secure_filename(input_file.filename)

    error_message: str
    try:
        if filename.lower().endswith(".xlsx"):
            temp_dir = Path(tempfile.gettempdir())
            saved_path = str(temp_dir / filename)
            input_file.save(saved_path)
            order_parser = ExcelOrderformParser()
            order_parser.parse_orderform(excel_path=saved_path)
        else:
            json_data = json.load(input_file.stream, strict=False)
            order_parser = JsonOrderformParser()
            order_parser.parse_orderform(order_data=json_data)
        parsed_order: Orderform = order_parser.generate_orderform()
    except (  # user misbehaviour
        AttributeError,
        OrderFormError,
        OverflowError,
        ValidationError,
        ValueError,
    ) as error:
        error_message = error.message if hasattr(error, "message") else str(error)
        LOG.error(error_message)
        http_error_response = HTTPStatus.BAD_REQUEST
    except (  # system misbehaviour
        NewConnectionError,
        MaxRetryError,
        TimeoutError,
        TypeError,
    ) as error:
        LOG.exception(error)
        error_message = error.message if hasattr(error, "message") else str(error)
        http_error_response = HTTPStatus.INTERNAL_SERVER_ERROR
    else:
        return jsonify(**parsed_order.model_dump())

    if error_message:
        return abort(make_response(jsonify(message=error_message), http_error_response))
