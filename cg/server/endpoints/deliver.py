from datetime import datetime
from http import HTTPStatus

from flask import Blueprint, Response, jsonify, request

from cg.server.endpoints.utils import before_request
from cg.server.ext import analysis_client, db
from cg.store.models import Analysis, Case

DELIVER_BLUEPRINT = Blueprint("deliver", __name__, url_prefix="/api/v1")
DELIVER_BLUEPRINT.before_request(before_request)


@DELIVER_BLUEPRINT.route("/deliver", methods=["POST"])
def deliver_analysis():
    """TODO
    - [ ] Filter samples, select the ones from the original case
    - [ ] Update the sample.delivered_at
    - [ ] Call trailblazer to mark the analysis as delivered
    - [ ] Commit changes to  StatusDb if TB call went well, else rollback
    """

    if trailblazer_id := request.args.get("trailblazer_id", type=int):
        analysis: Analysis = db.get_analysis_by_trailblazer_id(trailblazer_id)
        case: Case = analysis.case
        for case_sample in case.links:
            # TODO group meditation on attribute name
            if case_sample.is_original and not case_sample.sample.delivered_at:
                case_sample.sample.delivered_at = datetime.now()
        analysis_client.mark_analyses_as_delivered(trailblazer_ids=[trailblazer_id])
        return Response(status=HTTPStatus.NO_CONTENT)
    else:
        # TODO add test
        # TODO add error message shaming the bad request
        return jsonify({}), HTTPStatus.BAD_REQUEST
