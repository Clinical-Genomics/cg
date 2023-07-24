import http
import json
import logging
import tempfile
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from cachetools import TTLCache
from cg.apps.orderform.excel_orderform_parser import ExcelOrderformParser
from cg.apps.orderform.json_orderform_parser import JsonOrderformParser
from cg.constants import ANALYSIS_SOURCES, METAGENOME_SOURCES
from cg.constants.constants import FileFormat
from cg.exc import OrderError, OrderFormError, TicketCreationError
from cg.io.controller import WriteStream
from cg.meta.orders import OrdersAPI
from cg.models.orders.order import OrderIn, OrderType
from cg.models.orders.orderform_schema import Orderform
from cg.server.ext import db, lims, osticket
from cg.store.models import (
    Analysis,
    Application,
    Customer,
    Family,
    Flowcell,
    Pool,
    Sample,
    SampleLaneSequencingMetrics,
    User,
)
from flask import Blueprint, abort, current_app, g, jsonify, make_response, request
from google.auth import jwt
from pydantic.v1 import ValidationError
from requests.exceptions import HTTPError
from sqlalchemy.exc import IntegrityError
from urllib3.exceptions import MaxRetryError, NewConnectionError
from werkzeug.utils import secure_filename

LOG = logging.getLogger(__name__)
BLUEPRINT = Blueprint("api", __name__, url_prefix="/api/v1")

cache = TTLCache(maxsize=1, ttl=3600)
cache_certificates_key = "certs"
cache[cache_certificates_key] = None


def get_certificate_ttl(response_data) -> int:
    """Extract time to live in seconds for certificate from response headers."""
    expires_header = response_data.headers.get("Expires")
    expires = datetime.strptime(expires_header, "%a, %d %b %Y %H:%M:%S %Z")
    return int((expires - datetime.utcnow()).total_seconds())


def fetch_and_cache_google_oauth2_certificates():
    """Fetch and cache Google OAuth2 certificates."""
    global cache

    url = "https://www.googleapis.com/oauth2/v1/certs"
    response = requests.get(url)
    response.raise_for_status()

    certs = response.json()
    ttl = get_certificate_ttl(response_data=response)

    cache = TTLCache(maxsize=1, ttl=ttl)
    cache[cache_certificates_key] = certs

    return certs


def get_google_oauth2_certificates():
    """Get Google OAuth2 certificates from cache or fetch and cache them."""
    certs = cache.get(cache_certificates_key)

    if not certs:
        certs = fetch_and_cache_google_oauth2_certificates()

    return certs


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
            make_response(
                jsonify(message="Only https requests accepted"), http.HTTPStatus.FORBIDDEN
            )
        )

    if request.method == "OPTIONS":
        return make_response(jsonify(ok=True), http.HTTPStatus.NO_CONTENT)

    endpoint_func = current_app.view_functions[request.endpoint]
    if getattr(endpoint_func, "is_public", None):
        return

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return abort(
            make_response(
                jsonify(message="no JWT token found on request"), http.HTTPStatus.UNAUTHORIZED
            )
        )

    jwt_token = auth_header.split("Bearer ")[-1]
    try:
        user_data = jwt.decode(jwt_token, certs=get_google_oauth2_certificates())
    except ValueError as e:
        LOG.error(f"Error occurred while decoding JWT token: {e}")
        return abort(
            make_response(
                jsonify(message="outdated login certificate"), http.HTTPStatus.UNAUTHORIZED
            )
        )

    user: User = db.get_user_by_email(user_data["email"])
    if user is None or not user.order_portal_login:
        message = f"{user_data['email']} doesn't have access"
        LOG.error(message)
        return abort(make_response(jsonify(message=message), http.HTTPStatus.FORBIDDEN))

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
        project: OrderType = OrderType(order_type)
        order_in: OrderIn = OrderIn.parse_obj(request_json, project=project)

        result = api.submit(
            project=project,
            order_in=order_in,
            user_name=g.current_user.name,
            user_mail=g.current_user.email,
        )
    except (  # user misbehaviour
        OrderError,
        OrderFormError,
        ValidationError,
        ValueError,
    ) as error:
        error_message = error.message if hasattr(error, "message") else str(error)
        http_error_response = http.HTTPStatus.BAD_REQUEST
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
        http_error_response = http.HTTPStatus.INTERNAL_SERVER_ERROR
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

    customers: List[Customer] = _get_current_customers()
    cases: List[Family] = _get_cases(enquiry=enquiry, action=action, customers=customers)

    nr_cases: int = len(cases)
    cases_with_links: List[dict] = [case.to_dict(links=True) for case in cases]
    return jsonify(families=cases_with_links, total=nr_cases)


def _get_current_customers() -> Optional[List[Customer]]:
    """Return customers if the current user is not an admin."""
    return g.current_user.customers if not g.current_user.is_admin else None


def _get_cases(
    enquiry: Optional[str], action: Optional[str], customers: Optional[List[Customer]]
) -> List[Family]:
    """Get cases based on the provided filters."""
    return db.get_cases_by_customers_action_and_case_search(
        case_search=enquiry,
        customers=customers,
        action=action,
    )


@BLUEPRINT.route("/cases/<case_id>")
def parse_case(case_id):
    """Return a case with links."""
    case: Family = db.get_case_by_internal_id(internal_id=case_id)
    if case is None:
        return abort(http.HTTPStatus.NOT_FOUND)
    if not g.current_user.is_admin and (case.customer not in g.current_user.customers):
        return abort(http.HTTPStatus.FORBIDDEN)
    return jsonify(**case.to_dict(links=True, analyses=True))


@BLUEPRINT.route("/families_in_collaboration")
def parse_families_in_collaboration():
    """Return cases in collaboration."""

    customer_internal_id = request.args.get("customer")
    pipeline = request.args.get("data_analysis")
    case_search_pattern = request.args.get("enquiry")

    customer = db.get_customer_by_internal_id(customer_internal_id=customer_internal_id)

    cases = db.get_cases_by_customer_pipeline_and_case_search(
        case_search=case_search_pattern,
        customer=customer,
        pipeline=pipeline,
    )

    case_dicts = [case.to_dict(links=True) for case in cases]
    return jsonify(families=case_dicts, total=len(cases))


@BLUEPRINT.route("/families_in_collaboration/<family_id>")
def parse_family_in_collaboration(family_id):
    """Return a family with links."""
    case: Family = db.get_case_by_internal_id(internal_id=family_id)
    customer: Customer = db.get_customer_by_internal_id(
        customer_internal_id=request.args.get("customer")
    )
    if case.customer not in customer.collaborators:
        return abort(http.HTTPStatus.FORBIDDEN)
    return jsonify(**case.to_dict(links=True, analyses=True))


@BLUEPRINT.route("/samples")
def parse_samples():
    """Return samples."""
    if request.args.get("status") and not g.current_user.is_admin:
        return abort(http.HTTPStatus.FORBIDDEN)
    if request.args.get("status") == "incoming":
        samples: List[Sample] = db.get_samples_to_receive()
    elif request.args.get("status") == "labprep":
        samples: List[Sample] = db.get_samples_to_prepare()
    elif request.args.get("status") == "sequencing":
        samples: List[Sample] = db.get_samples_to_sequence()
    else:
        customers: Optional[List[Customer]] = (
            None if g.current_user.is_admin else g.current_user.customers
        )
        samples: List[Sample] = db.get_samples_by_customer_id_and_pattern(
            pattern=request.args.get("enquiry"), customers=customers
        )
    limit = int(request.args.get("limit", 50))
    parsed_samples: List[Dict] = [sample.to_dict() for sample in samples[:limit]]
    return jsonify(samples=parsed_samples, total=len(samples))


@BLUEPRINT.route("/samples_in_collaboration")
def parse_samples_in_collaboration():
    """Return samples in a customer group."""
    customer: Customer = db.get_customer_by_internal_id(
        customer_internal_id=request.args.get("customer")
    )
    samples: List[Sample] = db.get_samples_by_customer_id_and_pattern(
        pattern=request.args.get("enquiry"), customers=customer.collaborators
    )
    limit = int(request.args.get("limit", 50))
    parsed_samples: List[Dict] = [sample.to_dict() for sample in samples[:limit]]
    return jsonify(samples=parsed_samples, total=len(samples))


@BLUEPRINT.route("/samples/<sample_id>")
def parse_sample(sample_id):
    """Return a single sample."""
    sample: Sample = db.get_sample_by_internal_id(sample_id)
    if sample is None:
        return abort(http.HTTPStatus.NOT_FOUND)
    if not g.current_user.is_admin and (sample.customer not in g.current_user.customers):
        return abort(http.HTTPStatus.FORBIDDEN)
    return jsonify(**sample.to_dict(links=True, flowcells=True))


@BLUEPRINT.route("/samples_in_collaboration/<sample_id>")
def parse_sample_in_collaboration(sample_id):
    """Return a single sample."""
    sample: Sample = db.get_sample_by_internal_id(sample_id)
    customer: Customer = db.get_customer_by_internal_id(
        customer_internal_id=request.args.get("customer")
    )
    if sample.customer not in customer.collaborators:
        return abort(http.HTTPStatus.FORBIDDEN)
    return jsonify(**sample.to_dict(links=True, flowcells=True))


@BLUEPRINT.route("/pools")
def parse_pools():
    """Return pools."""
    customers: Optional[List[Customer]] = (
        g.current_user.customers if not g.current_user.is_admin else None
    )
    pools: List[Pool] = db.get_pools_to_render(
        customers=customers, enquiry=request.args.get("enquiry")
    )
    parsed_pools: List[Dict] = [pool_obj.to_dict() for pool_obj in pools[:30]]
    return jsonify(pools=parsed_pools, total=len(pools))


@BLUEPRINT.route("/pools/<pool_id>")
def parse_pool(pool_id):
    """Return a single pool."""
    pool: Pool = db.get_pool_by_entry_id(entry_id=pool_id)
    if pool is None:
        return abort(http.HTTPStatus.NOT_FOUND)
    if not g.current_user.is_admin and (pool.customer not in g.current_user.customers):
        return abort(http.HTTPStatus.FORBIDDEN)
    return jsonify(**pool.to_dict())


@BLUEPRINT.route("/flowcells")
def parse_flow_cells() -> Any:
    """Return flow cells."""
    flow_cells: List[Flowcell] = db.get_flow_cell_by_name_pattern_and_status(
        flow_cell_statuses=[request.args.get("status")],
        name_pattern=request.args.get("enquiry"),
    )
    parsed_flow_cells: List[Dict] = [flow_cell.to_dict() for flow_cell in flow_cells[:50]]
    return jsonify(flowcells=parsed_flow_cells, total=len(flow_cells))


@BLUEPRINT.route("/flowcells/<flowcell_id>")
def parse_flow_cell(flowcell_id):
    """Return a single flowcell."""
    flow_cell: Flowcell = db.get_flow_cell_by_name(flow_cell_name=flowcell_id)
    if flow_cell is None:
        return abort(http.HTTPStatus.NOT_FOUND)
    return jsonify(**flow_cell.to_dict(samples=True))


@BLUEPRINT.route("/flowcells/<flow_cell_name>/sequencing_metrics", methods=["GET"])
def get_sequencing_metrics(flow_cell_name: str):
    """Return sample lane sequencing metrics for a flow cell."""

    if not flow_cell_name:
        return jsonify({"error": "Invalid or missing flow cell id"}), http.HTTPStatus.BAD_REQUEST

    sequencing_metrics: List[
        SampleLaneSequencingMetrics
    ] = db.get_sample_lane_sequencing_metrics_by_flow_cell_name(flow_cell_name)

    if not sequencing_metrics:
        return (
            jsonify({"error": f"Sequencing metrics not found for flow cell {flow_cell_name}."}),
            http.HTTPStatus.NOT_FOUND,
        )

    return jsonify([metric.to_dict() for metric in sequencing_metrics])


@BLUEPRINT.route("/analyses")
def parse_analyses():
    """Return analyses."""
    if request.args.get("status") == "delivery":
        analyses: List[Analysis] = db.get_analyses_to_deliver_for_pipeline()
    elif request.args.get("status") == "upload":
        analyses: List[Analysis] = db.get_analyses_to_upload()
    else:
        analyses: List[Analysis] = db.get_analyses()
    parsed_analysis: List[Dict] = [analysis_obj.to_dict() for analysis_obj in analyses[:30]]
    return jsonify(analyses=parsed_analysis, total=len(analyses))


@BLUEPRINT.route("/options")
def parse_options():
    """Return various options."""
    customers: List[Optional[Customer]] = (
        db.get_customers() if g.current_user.is_admin else g.current_user.customers
    )

    app_tag_groups: Dict[str, List[str]] = {"ext": []}
    applications: List[Application] = db.get_applications_is_not_archived()
    for application in applications:
        if not application.versions:
            LOG.debug(f"Skipping application {application} that doesn't have a price")
            continue
        if application.is_external:
            app_tag_groups["ext"].append(application.tag)
        if application.prep_category not in app_tag_groups:
            app_tag_groups[application.prep_category]: List[str] = []
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
        return abort(http.HTTPStatus.FORBIDDEN)

    return jsonify(user=g.current_user.to_dict())


@BLUEPRINT.route("/applications")
@is_public
def parse_applications():
    """Return application tags."""
    applications: List[Application] = db.get_applications_is_not_archived()
    parsed_applications: List[Dict] = [application.to_dict() for application in applications]
    return jsonify(applications=parsed_applications)


@BLUEPRINT.route("/applications/<tag>")
@is_public
def parse_application(tag):
    """Return an application tag."""
    application: Application = db.get_application_by_tag(tag=tag)
    if application is None:
        return abort(
            make_response(jsonify(message="application not found"), http.HTTPStatus.NOT_FOUND)
        )
    return jsonify(**application.to_dict())


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
        http_error_response = http.HTTPStatus.BAD_REQUEST
    except (  # system misbehaviour
        NewConnectionError,
        MaxRetryError,
        TimeoutError,
        TypeError,
    ) as error:
        LOG.exception(error)
        error_message = error.message if hasattr(error, "message") else str(error)
        http_error_response = http.HTTPStatus.INTERNAL_SERVER_ERROR
    else:
        return jsonify(**parsed_order.dict())

    if error_message:
        return abort(make_response(jsonify(message=error_message), http_error_response))
