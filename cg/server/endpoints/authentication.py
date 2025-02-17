from http import HTTPStatus
from flask import jsonify, request, redirect, session, Blueprint

from cg.server.ext import auth_service
import logging

LOG = logging.getLogger(__name__)

AUTH_BLUEPRINT = Blueprint("auth", __name__, url_prefix="/auth")


@AUTH_BLUEPRINT.route("/login")
def login():
    """Redirect the user to the auth service login page."""
    auth_url = auth_service.get_auth_url()
    return redirect(auth_url)


@AUTH_BLUEPRINT.route("/callback")
def callback():
    """Callback route for the auth service."""
    code = request.args.get("code")
    if code:
        token = auth_service.get_token(code)
        session["token"] = token
        userinfo = auth_service.get_user_info(token)
        session["userinfo"] = userinfo
        return redirect("/")
    return (
            jsonify(error="You are not authorized to access this resource."),
            HTTPStatus.UNAUTHORIZED,
            )


@AUTH_BLUEPRINT.route("/logout")
def logout():
    """Logout the user from the auth service."""
    refresh_token = session.get("refresh_token")
    LOG.debug(f"refresh_token: {refresh_token}")
    if refresh_token:
        auth_service.logout_user(refresh_token)
    session.clear()
    return redirect("/")
