from flask import Blueprint, request

from cg.server.endpoints.utils import before_request

DELIVER_BLUEPRINT = Blueprint("deliver", __name__, url_prefix="/api/v1")
DELIVER_BLUEPRINT.before_request(before_request)


@DELIVER_BLUEPRINT.route("/deliver")  # TODO
def deliver_analysis():
    """TODO"""
    trailblazer_id: int | None = request.args.get("trailblazer_id", type=int)
    # TODO
    # - Get analysis.case.samples from trailblazer analysis ID
    # - Filter samples, select the ones from the original case
    # - Update the sample.delivered_at
    # - Call trailblazer to mark the analysis as delivered
    pass
