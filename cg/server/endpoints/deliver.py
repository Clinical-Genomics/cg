from http import HTTPStatus

from flask import Blueprint, Response, request

from cg.exc import AnalysisDoesNotExistError, TrailblazerAPIHTTPError
from cg.server.endpoints.utils import before_request
from cg.server.ext import db, mark_as_delivered_service
from cg.store.models import Analysis

DELIVER_BLUEPRINT = Blueprint("deliver", __name__, url_prefix="/api/v1")
DELIVER_BLUEPRINT.before_request(before_request)


@DELIVER_BLUEPRINT.route("/deliver", methods=["POST"])
def deliver_analyses():
    """..."""
    try:
        trailblazer_ids: list[int] = request.json["trailblazer_ids"]  # type: ignore None is handled
        analyses = []
        # TODO: decide if this logic belongs to this endpoint
        for trailblazer_id in trailblazer_ids:
            analysis: Analysis = db.get_analysis_by_trailblazer_id(trailblazer_id)
            analyses.append(analysis)
        mark_as_delivered_service.mark_analyses(analyses)
    except (AnalysisDoesNotExistError, KeyError, TypeError):
        return Response(status=HTTPStatus.BAD_REQUEST)
    except TrailblazerAPIHTTPError:
        db.rollback()
        return Response(status=HTTPStatus.BAD_GATEWAY)
    finally:
        db.commit_to_store()
    return Response(status=HTTPStatus.NO_CONTENT)
