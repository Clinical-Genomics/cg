# -*- coding: utf-8 -*-
from functools import wraps
from pathlib import Path
import tempfile

from flask import abort, current_app, Blueprint, jsonify, g, make_response, request
from google.auth import jwt
from werkzeug.utils import secure_filename

from cg.apps.orders import OrdersAPI
from cg.apps.lims import parse_orderform
from cg.exc import DuplicateRecordError
from .ext import db

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
        user_data = jwt.decode(jwt_token, verify=False)
        user_obj = db.user(user_data['email'])
        if user_obj is None:
            message = f"{user_data['email']} doesn't have access"
            return abort(make_response(jsonify(message=message), 403))
            make_response
        g.current_user = user_obj


@blueprint.route('/order', methods=['POST'])
def order():
    """Submit an order for samples."""
    api = OrdersAPI(lims=None, status=db)
    post_data = request.get_json()
    try:
        result = api.accept(post_data['type'], post_data['data'])
    except DuplicateRecordError as error:
        return abort(make_response(jsonify(message=error.message), 500))
    return jsonify(families=[family.to_dict() for family in result['families']])


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
    query = db.Family.query
    data = [family_obj.to_dict() for family_obj in query]
    return jsonify(families=data)


@blueprint.route('/families/<int:family_id>')
def family(family_id):
    """Fetch a family with links."""
    family_obj = db.Family.get(family_id)
    data = family_obj.to_dict(links=True)
    return jsonify(**data)


@blueprint.route('/samples')
def samples():
    """Fetch samples."""
    samples_q = db.samples(query=request.args.get('query'))
    data = [sample_obj.to_dict() for sample_obj in samples_q.limit(30)]
    return jsonify(samples=data)


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
    customer = None if g.current_user.is_admin else g.current_user.customer
    families = db.families(customer=customer)
    samples = db.samples(customer=customer)
    return jsonify(
        user=g.current_user.to_dict(),
        customer=g.current_user.customer.to_dict(),
        samples=[sample_obj.to_dict() for sample_obj in samples.limit(50)],
        families=[family_obj.to_dict() for family_obj in families.limit(50)]
    )


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
    project_data = parse_orderform(saved_path)
    project_data['name'] = filename
    return jsonify(**project_data)
