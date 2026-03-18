from http import HTTPStatus

from flask import Blueprint, Response, request

from cg.exc import AnalysisDoesNotExistError, TrailblazerAPIHTTPError
from cg.server.endpoints.utils import before_request
from cg.server.ext import db, mark_samples_as_delivered_service
from cg.store.models import Analysis

DELIVER_BLUEPRINT = Blueprint("deliver", __name__, url_prefix="/api/v1")
DELIVER_BLUEPRINT.before_request(before_request)


@DELIVER_BLUEPRINT.route("/deliver", methods=["POST"])
def deliver_analysis():
    """TODO
    - [x] Filter samples, select the ones from the original case
    - [x] Update the sample.delivered_at
    - [x] Call trailblazer to mark the analysis as delivered
    - [x] Commit changes to  StatusDb if TB call went well, else rollback
    """

    # TODO endpoint?
    trailblazer_id = request.args.get("trailblazer_id", type=int)
    if trailblazer_id is None:
        return Response(status=HTTPStatus.BAD_REQUEST)
    # TODO service?
    try:
        analysis: Analysis = db.get_analysis_by_trailblazer_id(trailblazer_id)
    except AnalysisDoesNotExistError:
        return Response(status=HTTPStatus.BAD_REQUEST)
    try:
        mark_samples_as_delivered_service.mark_samples_as_delivered(analysis)
    except TrailblazerAPIHTTPError:
        db.rollback()
        return Response(status=HTTPStatus.BAD_GATEWAY)
    finally:
        db.commit_to_store()
    return Response(status=HTTPStatus.NO_CONTENT)
