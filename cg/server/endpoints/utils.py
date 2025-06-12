import logging
from functools import wraps
from http import HTTPStatus

import cachecontrol
import requests
from flask import abort, current_app, g, jsonify, make_response, request
from google.auth import exceptions
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from cg.server.ext import db
from cg.store.models import User

LOG = logging.getLogger(__name__)

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
    except (exceptions.GoogleAuthError, ValueError) as e:
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
