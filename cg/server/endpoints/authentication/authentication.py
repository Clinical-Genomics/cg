from http import HTTPStatus
from flask import jsonify, request, redirect, session, Blueprint, url_for
from cg.server.endpoints.authentication.auth_error_handler import handle_auth_errors
from cg.server.ext import keycloak_client, auth_service


import logging

from cg.services.authentication.models import TokenResponseModel, UserInfo

LOG = logging.getLogger(__name__)

AUTH_BLUEPRINT = Blueprint("auth", __name__, url_prefix="/auth")


@AUTH_BLUEPRINT.route("/login")
@handle_auth_errors
def login():
    """Redirect the user to the auth service login page."""
    return redirect(keycloak_client.get_auth_url())


@AUTH_BLUEPRINT.route("/callback")
@handle_auth_errors
def callback():
    """Callback route for the auth service."""
    code = request.args.get("code")
    if code:
        token = keycloak_client.get_token(code)
        parsed_token = TokenResponseModel(**token)
        session["token"] = token
        user_info = UserInfo(**keycloak_client.get_user_info(parsed_token.access_token))
        session["user_info"] = user_info.model_dump()
        user_roles: list[str] = auth_service.get_user_roles(parsed_token.access_token)
        session["user_roles"] = user_roles
        return redirect("/")
    return (
        jsonify(error="You are not authorized to access this resource."),
        HTTPStatus.UNAUTHORIZED,
    )


@AUTH_BLUEPRINT.route("/logout")
@handle_auth_errors
def logout():
    """Logout the user from the auth service."""
    token = TokenResponseModel(**session.get("token"))
    keycloak_client.logout_user(token.refresh_token)
    session.clear()
    return redirect(url_for("admin.index"))
