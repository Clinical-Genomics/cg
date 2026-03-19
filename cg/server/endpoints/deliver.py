from http import HTTPStatus

from flask import Blueprint, Response, request

from cg.exc import AnalysisDoesNotExistError, TrailblazerAPIHTTPError
from cg.server.endpoints.utils import before_request
from cg.server.ext import db, mark_as_delivered_service
from cg.store.models import Analysis

DELIVER_BLUEPRINT = Blueprint("deliver", __name__, url_prefix="/api/v1")
DELIVER_BLUEPRINT.before_request(before_request)


@DELIVER_BLUEPRINT.route("/deliver", methods=["POST"])
def deliver_analysis():
    """..."""
    try:
        trailblazer_ids = request.json

        analysis: Analysis = db.get_analysis_by_trailblazer_id(trailblazer_ids)
        mark_as_delivered_service.mark_analysis(analysis)
    except (AnalysisDoesNotExistError, KeyError, ValueError):
        return Response(status=HTTPStatus.BAD_REQUEST)
    except TrailblazerAPIHTTPError:
        db.rollback()
        return Response(status=HTTPStatus.BAD_GATEWAY)
    finally:
        db.commit_to_store()
    return Response(status=HTTPStatus.NO_CONTENT)
