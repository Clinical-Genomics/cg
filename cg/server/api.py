# -*- coding: utf-8 -*-
from functools import wraps
from pathlib import Path
import tempfile

from flask import abort, current_app, Blueprint, jsonify, g, make_response, request
from google.auth import jwt
from werkzeug.utils import secure_filename

from cg.exc import DuplicateRecordError, OrderFormError, OrderError
from cg.apps.lims import parse_orderform
from cg.meta.orders import OrdersAPI, OrderType
from .ext import db, lims, osticket

blueprint = Blueprint('api', __name__, url_prefix='/api/v1')


def public(route_function):
    @wraps(route_function)
    def public_endpoint(*args, **kwargs):
        return route_function(*args, **kwargs)
    public_endpoint.is_public = True
    return public_endpoint


@blueprint.before_request
def before_request():
    """Authorize API routes with JSON Web Tokens."""
    if request.method == 'OPTIONS':
        return make_response(jsonify(ok=True), 204)

    endpoint_func = current_app.view_functions[request.endpoint]
    if not getattr(endpoint_func, 'is_public', None):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            jwt_token = auth_header.split('Bearer ')[-1]
        else:
            return abort(403, 'no JWT token found on request')
        try:
            user_data = jwt.decode(jwt_token, certs=current_app.config['GOOGLE_OAUTH_CERTS'])
        except ValueError as error:
            return abort(make_response(jsonify(message='outdated login certificate'), 403))
        user_obj = db.user(user_data['email'])
        if user_obj is None:
            message = f"{user_data['email']} doesn't have access"
            return abort(make_response(jsonify(message=message), 403))
        g.current_user = user_obj


@blueprint.route('/order/<order_type>', methods=['POST'])
def order(order_type):
    """Submit an order for samples."""
    api = OrdersAPI(lims=lims, status=db, osticket=osticket)
    post_data = request.get_json()
    try:
        name, email = g.current_user.name, g.current_user.email
        result = api.submit(OrderType[order_type.upper()], name, email, post_data)
    except (DuplicateRecordError, OrderError) as error:
        return abort(make_response(jsonify(message=error.message), 401))
    return jsonify(project=result['project'],
                   records=[record.to_dict() for record in result['records']])


@blueprint.route('/customers')
def customers():
    """Fetch customers."""
    query = db.Customer.query
    data = [record.to_dict() for record in query]
    return jsonify(customers=data)


@blueprint.route('/panels')
def panels():
    """Fetch panels."""
    query = db.Panel.query
    data = [record.to_dict() for record in query]
    return jsonify(panels=data)


@blueprint.route('/families')
def families():
    """Fetch families."""
    if request.args.get('status') == 'analysis':
        families_q = db.families_to_analyze()
    else:
        families_q = db.families(
            customer=(db.customer(request.args.get('customer')) if
                      request.args.get('customer') else None)
        )
    data = [family_obj.to_dict(links=True) for family_obj in families_q.limit(30)]
    return jsonify(families=data, total=families_q.count())


@blueprint.route('/families/<family_id>')
def family(family_id):
    """Fetch a family with links."""
    family_obj = db.family(family_id)
    data = family_obj.to_dict(links=True)
    return jsonify(**data)


@blueprint.route('/samples')
def samples():
    """Fetch samples."""
    if request.args.get('status') == 'incoming':
        samples_q = db.samples_to_recieve()
    elif request.args.get('status') == 'sequencing':
        samples_q = db.samples_to_sequence()
    else:
        samples_q = db.samples(
            query=request.args.get('query'),
            customer=(db.customer(request.args.get('customer')) if
                      request.args.get('customer') else None),
        )
    data = [sample_obj.to_dict() for sample_obj in samples_q.limit(30)]
    return jsonify(samples=data, total=samples_q.count())


@blueprint.route('/samples/<sample_id>')
def sample(sample_id):
    """Fetch a single sample."""
    sample_obj = db.sample(sample_id)
    if sample_obj is None:
        return abort(404)
    return jsonify(**sample_obj.to_dict())


@blueprint.route('/analyses')
def analyses():
    """Fetch analyses."""
    if request.args.get('status') == 'delivery':
        analyses_q = db.analyses_to_deliver()
    elif request.args.get('status') == 'upload':
        analyses_q = db.analyses_to_upload()
    else:
        analyses_q = db.Analysis.query
    data = [analysis_obj.to_dict() for analysis_obj in analyses_q.limit(30)]
    return jsonify(analyses=data, total=analyses_q.count())


@blueprint.route('/options')
def options():
    """Fetch various options."""
    customers = db.Customer.query if g.current_user.is_admin else [g.current_user.customer]
    return jsonify(
        customers=[{
            'text': f"{customer.name} ({customer.internal_id})",
            'value': customer.internal_id,
        } for customer in customers],
        applications=[application.tag for application in db.Application.query],
        panels=[panel.abbrev for panel in db.Panel.query],
    )


@blueprint.route('/me')
def me():
    """Fetch information about current user."""
    return jsonify(user=g.current_user.to_dict())


@blueprint.route('/applications')
@public
def applications():
    """Fetch application tags."""
    query = db.Application.query
    data = [record.to_dict() for record in query]
    return jsonify(applications=data)


@blueprint.route('/applications/<tag>')
@public
def application(tag):
    """Fetch an application tag."""
    record = db.application(tag)
    if record is None:
        return abort(make_response(jsonify(message='application not found'), 404))
    return jsonify(**record.to_dict())


@blueprint.route('/orderform', methods=['POST'])
def orderform():
    """Parse an orderform."""
    excel_file = request.files['file']
    filename = secure_filename(excel_file.filename)
    temp_dir = Path(tempfile.gettempdir())
    saved_path = str(temp_dir / filename)
    excel_file.save(saved_path)
    try:
        project_data = parse_orderform(saved_path)
    except OrderFormError as error:
        return abort(make_response(jsonify(message=error.message), 400))
    return jsonify(name=filename.rsplit('.')[0], **project_data)
