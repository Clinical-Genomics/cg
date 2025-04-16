from flask import Blueprint, jsonify, request

from cg.server.endpoints.utils import before_request
from cg.server.ext import db
from cg.store.models import Analysis

ANALYSES_BLUEPRINT = Blueprint("analyses", __name__, url_prefix="/api/v1")
ANALYSES_BLUEPRINT.before_request(before_request)


@ANALYSES_BLUEPRINT.route("/analyses")
def get_analyses():
    """Return analyses."""
    if request.args.get("status") == "delivery":
        analyses: list[Analysis] = db.get_analyses_to_deliver_for_pipeline()
    elif request.args.get("status") == "upload":
        analyses: list[Analysis] = db.get_analyses_to_upload()
    else:
        analyses: list[Analysis] = db.get_analyses()
    parsed_analysis: list[dict] = [analysis.to_dict() for analysis in analyses[:30]]
    return jsonify(analyses=parsed_analysis, total=len(analyses))
