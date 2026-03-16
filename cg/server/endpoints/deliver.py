from http import HTTPStatus

from flask import Blueprint, jsonify, request

from cg.server.endpoints.utils import before_request
from cg.server.ext import db

DELIVER_BLUEPRINT = Blueprint("deliver", __name__, url_prefix="/api/v1")
DELIVER_BLUEPRINT.before_request(before_request)


@DELIVER_BLUEPRINT.route("/deliver", methods=["POST"])  # TODO
def deliver_analysis():
    """TODO"""
    trailblazer_id: int | None = request.args.get("trailblazer_id", type=int)
    # TODO
    # - Get analysis.case.samples from trailblazer analysis ID

    # - Filter samples, select the ones from the original case
    # - Update the sample.delivered_at
    # - Call trailblazer to mark the analysis as delivered
    return jsonify({}), HTTPStatus.OK
