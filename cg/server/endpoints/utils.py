import logging
from functools import wraps
from http import HTTPStatus

import cachecontrol
import requests
from flask import abort, current_app, g, jsonify, make_response, request

from cg.server.ext import db
from cg.store.models import User
from cg.server.ext import keycloak_openid_client


LOG = logging.getLogger(__name__)

session = requests.session()
cached_session = cachecontrol.CacheControl(session)


def is_public(route_function):
    @wraps(route_function)
    def public_endpoint(*args, **kwargs):
        return route_function(*args, **kwargs)

    public_endpoint.is_public = True
    return public_endpoint


def test_keycloak_auth():
    token = keycloak_openid_client.token("christian.oertlin@scilifelab.se", "password")
    print(f"keycloak token {token}")


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
    test_keycloak_auth()
    # # replace
    # try:
    #     user_data = verify_google_token(jwt_token)
    # except (exceptions.OAuthError, ValueError) as e:
    #     LOG.error(f"Error {e} occurred while decoding JWT token: {jwt_token}")
    #     return abort(
    #         make_response(jsonify(message="outdated login certificate"), HTTPStatus.UNAUTHORIZED)
    #     )
    user_data = {"email": "ahmed.amin@scilifelab.se"}
    user: User = db.get_user_by_email(user_data["email"])
    if user is None or not user.order_portal_login:
        message = f"{user_data['email']} doesn't have access"
        LOG.error(message)
        return abort(make_response(jsonify(message=message), HTTPStatus.FORBIDDEN))

    g.current_user = user
