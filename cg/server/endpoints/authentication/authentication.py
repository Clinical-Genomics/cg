from http import HTTPStatus
from flask import jsonify, request, redirect, session, Blueprint, flash, url_for
from keycloak import KeycloakConnectionError, KeycloakGetError
from pydantic import ValidationError
from cg import exc
from cg.server.ext import keycloak_client


import logging

from cg.services.authentication.models import TokenResponseModel, UserInfo

LOG = logging.getLogger(__name__)

AUTH_BLUEPRINT = Blueprint("auth", __name__, url_prefix="/auth")


@AUTH_BLUEPRINT.route("/login")
def login():
    """Redirect the user to the auth service login page."""
    return redirect(keycloak_client.get_auth_url())
    

@AUTH_BLUEPRINT.route("/callback")
def callback():
    """Callback route for the auth service."""
    code = request.args.get("code")

    if code:
        token = keycloak_client.get_token(code)
        parsed_token = TokenResponseModel(**token)
        session["token"] = token        
        userinfo = keycloak_client.get_user_info(parsed_token.access_token)
        session["userinfo"] = userinfo
        return redirect("/")
    return (
            jsonify(error="You are not authorized to access this resource."),
            HTTPStatus.UNAUTHORIZED,
         ) 
    
        


@AUTH_BLUEPRINT.route("/logout")
def logout():
    """Logout the user from the auth service."""
    try:
        refresh_token = session.get("refresh_token")
        if refresh_token:
            keycloak_client.logout_user(refresh_token)
            session.clear()
            return redirect("/")
        return (
            jsonify(error="You are not authorized to access this resource."),
            HTTPStatus.UNAUTHORIZED,
         ) 
    except KeycloakGetError as error:
        flash(f"Logout failed. {error}")
        return redirect("/")
    except Exception as error:
        flash(f"Logout failed. {error}")
        return redirect("/")