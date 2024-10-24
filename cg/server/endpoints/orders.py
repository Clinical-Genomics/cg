import json
import logging
import tempfile
from http import HTTPStatus
from pathlib import Path

from flask import Blueprint, abort, g, jsonify, make_response, request
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
    OrderError,
    OrderExistsError,
    OrderFormError,
    OrderNotDeliverableError,
    OrderNotFoundError,
    TicketCreationError,
)
from cg.io.controller import WriteStream
from cg.meta.orders import OrdersAPI
from cg.models.orders.order import OrderIn, OrderType
from cg.models.orders.orderform_schema import Orderform
from cg.server.dto.delivery_message.delivery_message_response import (
    DeliveryMessageResponse,
)
from cg.server.dto.orders.order_delivery_update_request import OrderOpenUpdateRequest
from cg.server.dto.orders.order_patch_request import OrderOpenPatch
from cg.server.dto.orders.orders_request import OrdersRequest
from cg.server.dto.orders.orders_response import Order, OrdersResponse
from cg.server.endpoints.utils import before_request
from cg.server.ext import (
    db,
    delivery_message_service,
    lims,
    order_service,
    order_submitter_registry,
    ticket_handler,
)
from cg.store.models import Application, Customer

ORDERS_BLUEPRINT = Blueprint("orders", __name__, url_prefix="/api/v1")
ORDERS_BLUEPRINT.before_request(before_request)

LOG = logging.getLogger(__name__)


@ORDERS_BLUEPRINT.route("/orders")
def get_orders():
    """Return the latest orders."""
    data = OrdersRequest.model_validate(request.args.to_dict())
    response: OrdersResponse = order_service.get_orders(data)
    return make_response(response.model_dump())


@ORDERS_BLUEPRINT.route("/orders/<order_id>")
def get_order(order_id: int):
    """Return an order."""
    try:
        response: Order = order_service.get_order(order_id)
        response_dict: dict = response.model_dump()
        return make_response(response_dict)
    except OrderNotFoundError as error:
        return make_response(jsonify(error=str(error)), HTTPStatus.NOT_FOUND)


@ORDERS_BLUEPRINT.route("/orders/<order_id>/open", methods=["PATCH"])
def set_order_open(order_id: int):
    try:
        request_data = OrderOpenPatch.model_validate(request.json)
        is_open: bool = request_data.open
        response_data: Order = order_service.set_open(order_id=order_id, open=is_open)
        return jsonify(response_data.model_dump()), HTTPStatus.OK
    except OrderNotFoundError as error:
        return jsonify(error=str(error)), HTTPStatus.NOT_FOUND


@ORDERS_BLUEPRINT.route("/orders/<order_id>/update-open-status", methods=["POST"])
def update_order_open(order_id: int):
    """Update the is_open parameter of an order based on the number of delivered analyses."""
    try:
        request_data = OrderOpenUpdateRequest.model_validate(request.json)
        delivered_analyses: int = request_data.delivered_analyses_count
        order_service.update_is_open(order_id=order_id, delivered_analyses=delivered_analyses)
    except OrderNotFoundError as error:
        return jsonify(error=str(error)), HTTPStatus.NOT_FOUND


@ORDERS_BLUEPRINT.route("/orders/<order_id>/delivery_message")
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


@ORDERS_BLUEPRINT.route("/orderform", methods=["POST"])
def create_order_from_form():
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


@ORDERS_BLUEPRINT.route("/submit_order/<order_type>", methods=["POST"])
def submit_order(order_type):
    """Submit an order for samples."""
    api = OrdersAPI(
        lims=lims,
        status=db,
        ticket_handler=ticket_handler,
        submitter_registry=order_submitter_registry,
    )
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
        existing_ticket: str | None = ticket_handler.parse_ticket_number(order_in.name)
        if existing_ticket and order_service.store.get_order_by_ticket_id(existing_ticket):
            raise OrderExistsError(f"Order with ticket id {existing_ticket} already exists.")

        result: dict = api.submit(
            project=project,
            order_in=order_in,
            user_name=g.current_user.name,
            user_mail=g.current_user.email,
        )

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


@ORDERS_BLUEPRINT.route("/options")
def get_options():
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
