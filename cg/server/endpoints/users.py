import logging
from http import HTTPStatus
from flask import Blueprint, abort, g, jsonify

from cg.server.endpoints.utils import before_request

LOG = logging.getLogger(__name__)
USERS_BLUEPRINT = Blueprint("users", __name__, url_prefix="/api/v1")
USERS_BLUEPRINT.before_request(before_request)


@USERS_BLUEPRINT.route("/me")
def get_user_information():
    """Return information about current user."""
    if not g.current_user.is_admin and not g.current_user.customers:
        LOG.error(
            "%s is not admin and is not connected to any customers, aborting", g.current_user.email
        )
        return abort(HTTPStatus.FORBIDDEN)

    return jsonify(user=g.current_user.to_dict())
