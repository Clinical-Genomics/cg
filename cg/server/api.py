# -*- coding: utf-8 -*-
import json
import logging
from functools import wraps
from pathlib import Path
import tempfile

from cg.constants import METAGENOME_SOURCES, ANALYSIS_SOURCES
from flask import abort, current_app, Blueprint, jsonify, g, make_response, request
from google.auth import jwt
from requests.exceptions import HTTPError
from werkzeug.utils import secure_filename

from cg.exc import DuplicateRecordError, OrderFormError, OrderError
from cg.apps.lims import parse_orderform, parse_json
from cg.meta.orders import OrdersAPI, OrderType
from .ext import db, lims, osticket

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
        return make_response(jsonify(ok=True), 204)

    endpoint_func = current_app.view_functions[request.endpoint]
    if not getattr(endpoint_func, "is_public", None):
        auth_header = request.headers.get("Authorization")
        if auth_header:
            jwt_token = auth_header.split("Bearer ")[-1]
        else:
            return abort(403, "no JWT token found on request")
        try:
            user_data = jwt.decode(jwt_token, certs=current_app.config["GOOGLE_OAUTH_CERTS"])
        except ValueError as error:
            return abort(make_response(jsonify(message="outdated login certificate"), 403))
        user_obj = db.user(user_data["email"])
        if user_obj is None:
            message = f"{user_data['email']} doesn't have access"
            return abort(make_response(jsonify(message=message), 403))
        g.current_user = user_obj


@BLUEPRINT.route("/submit_order/<order_type>", methods=["POST"])
def submit_order(order_type):
    """Submit an order for samples."""
    api = OrdersAPI(lims=lims, status=db, osticket=osticket)
    post_data = request.get_json()
    LOG.info("processing '%s' order: %s", order_type, post_data)
    try:
        ticket = {"name": g.current_user.name, "email": g.current_user.email}
        result = api.submit(OrderType(order_type), post_data, ticket=ticket)
    except (DuplicateRecordError, OrderError) as error:
        return abort(make_response(jsonify(message=error.message), 401))
    except HTTPError as error:
        return abort(make_response(jsonify(message=error.args[0]), 401))

    return jsonify(
        project=result["project"], records=[record.to_dict() for record in result["records"]]
    )


@BLUEPRINT.route("/customers")
def customers():
    """Fetch customers."""
    query = db.Customer.query
    data = [record.to_dict() for record in query]
    return jsonify(customers=data)


@BLUEPRINT.route("/panels")
def panels():
    """Fetch panels."""
    query = db.Panel.query
    data = [record.to_dict() for record in query]
    return jsonify(panels=data)


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
        customer_obj = None if g.current_user.is_admin else g.current_user.customer
        families_q = db.families(
            enquiry=request.args.get("enquiry"),
            customer=customer_obj,
            action=request.args.get("action"),
        )
        count = families_q.count()
        records = families_q.limit(30)
    data = [family_obj.to_dict(links=True) for family_obj in records]
    return jsonify(families=data, total=count)


@BLUEPRINT.route("/families_in_customer_group")
def families_in_customer_group():
    """Fetch families in customer_group."""
    customer_obj = None if g.current_user.is_admin else g.current_user.customer
    families_q = db.families_in_customer_group(
        enquiry=request.args.get("enquiry"), customer=customer_obj
    )
    count = families_q.count()
    records = families_q.limit(30)
    data = [family_obj.to_dict(links=True) for family_obj in records]
    return jsonify(families=data, total=count)


@BLUEPRINT.route("/families/<family_id>")
def family(family_id):
    """Fetch a family with links."""
    family_obj = db.family(family_id)
    if family_obj is None:
        return abort(404)
    elif not g.current_user.is_admin and (g.current_user.customer != family_obj.customer):
        return abort(401)

    data = family_obj.to_dict(links=True, analyses=True)
    return jsonify(**data)


@BLUEPRINT.route("/families_in_customer_group/<family_id>")
def family_in_customer_group(family_id):
    """Fetch a family with links."""
    family_obj = db.family(family_id)
    if family_obj is None:
        return abort(404)
    elif not g.current_user.is_admin and (
        g.current_user.customer.customer_group != family_obj.customer.customer_group
    ):
        return abort(401)

    data = family_obj.to_dict(links=True, analyses=True)
    return jsonify(**data)


@BLUEPRINT.route("/samples")
def samples():
    """Fetch samples."""
    if request.args.get("status") and not g.current_user.is_admin:
        return abort(401)
    if request.args.get("status") == "incoming":
        samples_q = db.samples_to_receive()
    elif request.args.get("status") == "labprep":
        samples_q = db.samples_to_prepare()
    elif request.args.get("status") == "sequencing":
        samples_q = db.samples_to_sequence()
    else:
        customer_obj = None if g.current_user.is_admin else g.current_user.customer
        samples_q = db.samples(enquiry=request.args.get("enquiry"), customer=customer_obj)
    limit = int(request.args.get("limit", 50))
    data = [sample_obj.to_dict() for sample_obj in samples_q.limit(limit)]
    return jsonify(samples=data, total=samples_q.count())


@BLUEPRINT.route("/samples_in_customer_group")
def samples_in_customer_group():
    """Fetch samples in a customer group."""
    customer_obj = None if g.current_user.is_admin else g.current_user.customer
    samples_q = db.samples_in_customer_group(
        enquiry=request.args.get("enquiry"), customer=customer_obj
    )
    limit = int(request.args.get("limit", 50))
    data = [sample_obj.to_dict() for sample_obj in samples_q.limit(limit)]
    return jsonify(samples=data, total=samples_q.count())


@BLUEPRINT.route("/samples/<sample_id>")
def sample(sample_id):
    """Fetch a single sample."""
    sample_obj = db.sample(sample_id)
    if sample_obj is None:
        return abort(404)
    elif not g.current_user.is_admin and (g.current_user.customer != sample_obj.customer):
        return abort(401)
    data = sample_obj.to_dict(links=True, flowcells=True)
    return jsonify(**data)


@BLUEPRINT.route("/samples_in_customer_group/<sample_id>")
def sample_in_customer_group(sample_id):
    """Fetch a single sample."""
    sample_obj = db.sample(sample_id)
    if sample_obj is None:
        return abort(404)
    elif not g.current_user.is_admin and (
        g.current_user.customer.customer_group != sample_obj.customer.customer_group
    ):
        return abort(401)
    data = sample_obj.to_dict(links=True, flowcells=True)
    return jsonify(**data)


@BLUEPRINT.route("/pools")
def pools():
    """Fetch pools."""
    customer_obj = None if g.current_user.is_admin else g.current_user.customer
    pools_q = db.pools(customer=customer_obj, enquiry=request.args.get("enquiry"))
    data = [pool_obj.to_dict() for pool_obj in pools_q.limit(30)]
    return jsonify(pools=data, total=pools_q.count())


@BLUEPRINT.route("/pools/<pool_id>")
def pool(pool_id):
    """Fetch a single pool."""
    record = db.pool(pool_id)
    if record is None:
        return abort(404)
    elif not g.current_user.is_admin and (g.current_user.customer != record.customer):
        return abort(401)
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
    record = db.flowcell(flowcell_id)
    if record is None:
        return abort(404)
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
    customer_objs = (
        db.Customer.query.all() if g.current_user.is_admin else [g.current_user.customer]
    )
    apptag_groups = {"ext": []}
    for application_obj in db.applications(archived=False):
        if application_obj.is_external:
            apptag_groups["ext"].append(application_obj.tag)
        else:
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
        return abort(make_response(jsonify(message="application not found"), 404))
    return jsonify(**record.to_dict())


@BLUEPRINT.route("/orderform", methods=["POST"])
def orderform():
    """Parse an orderform/JSON export."""
    input_file = request.files.get("file")
    filename = secure_filename(input_file.filename)

    try:
        if filename.lower().endswith(".xlsx"):
            temp_dir = Path(tempfile.gettempdir())
            saved_path = str(temp_dir / filename)
            input_file.save(saved_path)
            project_data = parse_orderform(saved_path)
        else:
            json_data = json.load(input_file.stream)
            project_data = parse_json(json_data)
    except OrderFormError as error:
        return abort(make_response(jsonify(message=error.message), 400))

    return jsonify(**project_data)
