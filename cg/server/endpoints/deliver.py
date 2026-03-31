import logging
from http import HTTPStatus

import requests
from flask import Blueprint, Response, jsonify, request

from cg.exc import AnalysisDoesNotExistError, TrailblazerAPIHTTPError
from cg.server.endpoints.utils import before_request
from cg.server.ext import db, mark_as_delivered_service
from cg.store.models import Analysis

DELIVER_BLUEPRINT = Blueprint("deliver", __name__, url_prefix="/api/v1")
DELIVER_BLUEPRINT.before_request(before_request)

LOG = logging.getLogger(__name__)


@DELIVER_BLUEPRINT.route("/deliver", methods=["POST"])
def deliver_analyses():
    """
    Marks the analyses as delivered.
    - Adds a date stamp to the 'delivered_at' field for the relevant samples.
    - Calls Trailblazer to mark the Trailblazer analyses entries as delivered.
    """
    try:
        trailblazer_ids: list[int] = request.json["trailblazer_ids"]  # type: ignore None is handled
        analyses = []
        for trailblazer_id in trailblazer_ids:
            analysis: Analysis = db.get_analysis_by_trailblazer_id(trailblazer_id)
            analyses.append(analysis)
        analyses_response: requests.Response = mark_as_delivered_service.mark_analyses(analyses)
    except AnalysisDoesNotExistError as error:
        LOG.error(str(error))
        return jsonify(message=str(error)), HTTPStatus.BAD_REQUEST
    except (KeyError, TypeError):
        return Response(status=HTTPStatus.BAD_REQUEST)
    except TrailblazerAPIHTTPError as error:
        LOG.error(f"Error in Trailblazer: {str(error)} - rolling back changes in StatusDB.")
        db.rollback()
        return jsonify(message="Error when calling Trailblazer"), HTTPStatus.BAD_GATEWAY
    finally:
        db.commit_to_store()
    return jsonify(analyses_response), analyses_response.status_code
