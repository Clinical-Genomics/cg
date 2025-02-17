import logging
from functools import wraps
from http import HTTPStatus

import cachecontrol
from keycloak import KeycloakError
import requests
from flask import abort, current_app, g, jsonify, make_response, request

from cg.server.ext import auth_service
from cg.store.models import User


LOG = logging.getLogger(__name__)

session = requests.session()
cached_session = cachecontrol.CacheControl(session)


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
        user: User = auth_service.verify_token(jwt_token)
    except ValueError as error:
        return abort(make_response(jsonify(message=str(error)), HTTPStatus.FORBIDDEN))
    except KeycloakError as error:
        return abort(make_response(jsonify(message=str(error)), HTTPStatus.UNAUTHORIZED))
    except Exception as error:
        return abort(make_response(jsonify(message=str(error)), HTTPStatus.INTERNAL_SERVER_ERROR))

    g.current_user = user
