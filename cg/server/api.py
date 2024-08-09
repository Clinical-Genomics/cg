import logging
from http import HTTPStatus
from flask import Blueprint, abort, g, jsonify, request

from cg.server.ext import db
from cg.server.endpoints.utils import before_request
from cg.store.models import Analysis

LOG = logging.getLogger(__name__)
BLUEPRINT = Blueprint("api", __name__, url_prefix="/api/v1")
BLUEPRINT.before_request(before_request)


@BLUEPRINT.route("/analyses")
def get_analyses():
    """Return analyses."""
    if request.args.get("status") == "delivery":
        analyses: list[Analysis] = db.get_analyses_to_deliver_for_pipeline()
    elif request.args.get("status") == "upload":
        analyses: list[Analysis] = db.get_analyses_to_upload()
    else:
        analyses: list[Analysis] = db.get_analyses()
    parsed_analysis: list[dict] = [analysis_obj.to_dict() for analysis_obj in analyses[:30]]
    return jsonify(analyses=parsed_analysis, total=len(analyses))


@BLUEPRINT.route("/me")
def get_user_information():
    """Return information about current user."""
    if not g.current_user.is_admin and not g.current_user.customers:
        LOG.error(
            "%s is not admin and is not connected to any customers, aborting", g.current_user.email
        )
        return abort(HTTPStatus.FORBIDDEN)

    return jsonify(user=g.current_user.to_dict())
