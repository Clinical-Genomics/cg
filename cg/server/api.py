import http
import logging
import json
import tempfile
from functools import wraps
from pathlib import Path
from typing import List, Optional

import requests
from sqlalchemy.exc import IntegrityError
from urllib3.exceptions import MaxRetryError, NewConnectionError

from cg.apps.orderform.excel_orderform_parser import ExcelOrderformParser
from cg.apps.orderform.json_orderform_parser import JsonOrderformParser
from cg.constants import ANALYSIS_SOURCES, METAGENOME_SOURCES
from cg.constants.constants import FileFormat
from cg.exc import OrderError, OrderFormError, TicketCreationError
from cg.server.ext import db, lims, osticket
from cg.io.controller import WriteStream, ReadStream
from cg.meta.orders import OrdersAPI
from cg.models.orders.order import OrderIn, OrderType
from cg.models.orders.orderform_schema import Orderform
from cg.store import models
from flask import Blueprint, abort, current_app, g, jsonify, make_response, request
from google.auth import jwt
from pydantic import ValidationError
from requests.exceptions import HTTPError
from sqlalchemy.orm import Query
from werkzeug.utils import secure_filename

LOG = logging.getLogger(__name__)
BLUEPRINT = Blueprint("api", __name__, url_prefix="/api/v1")


def public(route_function):
    @wraps(route_function)
    def public_endpoint(*args, **kwargs):
        return route_function(*args, **kwargs)

    public_endpoint.is_public = True
    return public_endpoint


@BLUEPRINT.before_request
def before_request():
    """Authorize API routes with JSON Web Tokens."""
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
        user_data = jwt.decode(
            jwt_token, certs=requests.get("https://www.googleapis.com/oauth2/v1/certs").json()
        )
    except ValueError:
        return abort(
            make_response(
                jsonify(message="outdated login certificate"), http.HTTPStatus.UNAUTHORIZED
            )
        )

    user_obj = db.user(user_data["email"])
    if user_obj is None or not user_obj.order_portal_login:
        message = f"{user_data['email']} doesn't have access"
        LOG.error(message)
        return abort(make_response(jsonify(message=message), http.HTTPStatus.FORBIDDEN))

    g.current_user = user_obj


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
def cases():
    """Fetch cases."""
    records = db.cases(days=31)
    count = len(records)
    return jsonify(cases=records, total=count)


@BLUEPRINT.route("/families")
def families():
    """Fetch families."""
    if request.args.get("status") == "analysis":
        records = db.cases_to_mip_analyze()
        count = len(records)
    else:
        customer_objs: Optional[List[models.Customer]] = (
            None if g.current_user.is_admin else g.current_user.customers
        )
        case_query = db.families(
            enquiry=request.args.get("enquiry"),
            customers=customer_objs,
            action=request.args.get("action"),
        )
        count = case_query.count()
        records = case_query.limit(30)

    cases_data: List[dict] = [case_obj.to_dict(links=True) for case_obj in records]
    return jsonify(families=cases_data, total=count)


@BLUEPRINT.route("/families_in_collaboration")
def families_in_collaboration():
    """Fetch families in collaboration."""
    order_customer: models.Customer = db.customer(request.args.get("customer"))
    data_analysis: str = request.args.get("data_analysis")
    families_q: Query = db.families(
        enquiry=request.args.get("enquiry"),
        customers=order_customer.collaborators,
        data_analysis=data_analysis,
    )
    count = families_q.count()
    records = families_q.limit(30)
    data = [case_obj.to_dict(links=True) for case_obj in records]
    return jsonify(families=data, total=count)


@BLUEPRINT.route("/families/<family_id>")
def family(family_id):
    """Fetch a family with links."""
    case_obj = db.family(family_id)
    if case_obj is None:
        return abort(http.HTTPStatus.NOT_FOUND)
    if not g.current_user.is_admin and (case_obj.customer not in g.current_user.customers):
        return abort(http.HTTPStatus.FORBIDDEN)

    data = case_obj.to_dict(links=True, analyses=True)
    return jsonify(**data)


@BLUEPRINT.route("/families_in_collaboration/<family_id>")
def family_in_collaboration(family_id):
    """Fetch a family with links."""
    case_obj = db.family(family_id)
    order_customer = db.customer(request.args.get("customer"))
    if case_obj.customer not in order_customer.collaborators:
        return abort(http.HTTPStatus.FORBIDDEN)
    data = case_obj.to_dict(links=True, analyses=True)
    return jsonify(**data)


@BLUEPRINT.route("/samples")
def samples():
    """Fetch samples."""
    if request.args.get("status") and not g.current_user.is_admin:
        return abort(http.HTTPStatus.FORBIDDEN)
    if request.args.get("status") == "incoming":
        samples_q = db.samples_to_receive()
    elif request.args.get("status") == "labprep":
        samples_q = db.samples_to_prepare()
    elif request.args.get("status") == "sequencing":
        samples_q = db.samples_to_sequence()
    else:
        customer_objs: Optional[models.Customer] = (
            None if g.current_user.is_admin else g.current_user.customers
        )
        samples_q = db.samples(enquiry=request.args.get("enquiry"), customers=customer_objs)
    limit = int(request.args.get("limit", 50))
    data = [sample_obj.to_dict() for sample_obj in samples_q.limit(limit)]
    return jsonify(samples=data, total=samples_q.count())


@BLUEPRINT.route("/samples_in_collaboration")
def samples_in_collaboration():
    """Fetch samples in a customer group."""
    order_customer = db.customer(request.args.get("customer"))
    samples_q = db.samples(
        enquiry=request.args.get("enquiry"), customers=order_customer.collaborators
    )
    limit = int(request.args.get("limit", 50))
    data = [sample_obj.to_dict() for sample_obj in samples_q.limit(limit)]
    return jsonify(samples=data, total=samples_q.count())


@BLUEPRINT.route("/samples/<sample_id>")
def sample(sample_id):
    """Fetch a single sample."""
    sample_obj = db.sample(sample_id)
    if sample_obj is None:
        return abort(http.HTTPStatus.NOT_FOUND)
    if not g.current_user.is_admin and (sample_obj.customer not in g.current_user.customers):
        return abort(http.HTTPStatus.FORBIDDEN)
    data = sample_obj.to_dict(links=True, flowcells=True)
    return jsonify(**data)


@BLUEPRINT.route("/samples_in_collaboration/<sample_id>")
def sample_in_collaboration(sample_id):
    """Fetch a single sample."""
    sample_obj = db.sample(sample_id)
    order_customer = db.customer(request.args.get("customer"))
    if sample_obj.customer not in order_customer.collaborators:
        return abort(http.HTTPStatus.FORBIDDEN)
    data = sample_obj.to_dict(links=True, flowcells=True)
    return jsonify(**data)


@BLUEPRINT.route("/pools")
def pools():
    """Fetch pools."""
    customer_objs: Optional[models.Customer] = (
        None if g.current_user.is_admin else g.current_user.customers
    )
    pools_q = db.pools(customers=customer_objs, enquiry=request.args.get("enquiry"))
    data = [pool_obj.to_dict() for pool_obj in pools_q.limit(30)]
    return jsonify(pools=data, total=pools_q.count())


@BLUEPRINT.route("/pools/<pool_id>")
def pool(pool_id):
    """Fetch a single pool."""
    record = db.pool(pool_id)
    if record is None:
        return abort(http.HTTPStatus.NOT_FOUND)
    if not g.current_user.is_admin and (record.customer not in g.current_user.customers):
        return abort(http.HTTPStatus.FORBIDDEN)
    return jsonify(**record.to_dict())


@BLUEPRINT.route("/flowcells")
def flowcells():
    """Fetch flowcells."""
    query = db.flowcells(status=request.args.get("status"), enquiry=request.args.get("enquiry"))
    data = [record.to_dict() for record in query.limit(50)]
    return jsonify(flowcells=data, total=query.count())


@BLUEPRINT.route("/flowcells/<flowcell_id>")
def flowcell(flowcell_id):
    """Fetch a single flowcell."""
    record = db.get_flow_cell(flowcell_id)
    if record is None:
        return abort(http.HTTPStatus.NOT_FOUND)
    return jsonify(**record.to_dict(samples=True))


@BLUEPRINT.route("/analyses")
def analyses():
    """Fetch analyses."""
    if request.args.get("status") == "delivery":
        analyses_q = db.analyses_to_deliver()
    elif request.args.get("status") == "upload":
        analyses_q = db.analyses_to_upload()
    else:
        analyses_q = db.Analysis.query
    data = [analysis_obj.to_dict() for analysis_obj in analyses_q.limit(30)]
    return jsonify(analyses=data, total=analyses_q.count())


@BLUEPRINT.route("/options")
def options():
    """Fetch various options."""
    customer_objs: Optional[models.Customer] = (
        db.Customer.query.all() if g.current_user.is_admin else g.current_user.customers
    )

    apptag_groups = {"ext": []}
    for application_obj in db.applications(archived=False):

        if not application_obj.versions:
            LOG.debug("Skipping application %s that doesn't have a price", application)
            continue
        if application_obj.is_external:
            apptag_groups["ext"].append(application_obj.tag)
        if application_obj.prep_category not in apptag_groups:
            apptag_groups[application_obj.prep_category] = []
        apptag_groups[application_obj.prep_category].append(application_obj.tag)

    source_groups = {"metagenome": METAGENOME_SOURCES, "analysis": ANALYSIS_SOURCES}

    return jsonify(
        customers=[
            {"text": f"{customer.name} ({customer.internal_id})", "value": customer.internal_id}
            for customer in customer_objs
        ],
        applications=apptag_groups,
        panels=[panel.abbrev for panel in db.panels()],
        organisms=[
            {
                "name": organism.name,
                "reference_genome": organism.reference_genome,
                "internal_id": organism.internal_id,
                "verified": organism.verified,
            }
            for organism in db.organisms()
        ],
        sources=source_groups,
        beds=[bed.name for bed in db.beds(hide_archived=True)],
    )


@BLUEPRINT.route("/me")
def me():
    """Fetch information about current user."""
    if not g.current_user.is_admin and not g.current_user.customers:
        LOG.error(
            "%s is not admin and is not connected to any customers, aborting", g.current_user.email
        )
        return abort(http.HTTPStatus.FORBIDDEN)

    return jsonify(user=g.current_user.to_dict())


@BLUEPRINT.route("/applications")
@public
def applications():
    """Fetch application tags."""
    query = db.applications(archived=False)
    data = [record.to_dict() for record in query]
    return jsonify(applications=data)


@BLUEPRINT.route("/applications/<tag>")
@public
def application(tag):
    """Fetch an application tag."""
    record = db.application(tag)
    if record is None:
        return abort(
            make_response(jsonify(message="application not found"), http.HTTPStatus.NOT_FOUND)
        )
    return jsonify(**record.to_dict())


@BLUEPRINT.route("/orderform", methods=["POST"])
def orderform():
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
