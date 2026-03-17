from datetime import datetime
from http import HTTPStatus

from flask import Blueprint, Response, jsonify, request

from cg.constants import Workflow
from cg.exc import TrailblazerAPIHTTPError
from cg.server.endpoints.utils import before_request
from cg.server.ext import analysis_client, db
from cg.store.models import Analysis, Case, CaseSample

DELIVER_BLUEPRINT = Blueprint("deliver", __name__, url_prefix="/api/v1")
DELIVER_BLUEPRINT.before_request(before_request)


@DELIVER_BLUEPRINT.route("/deliver", methods=["POST"])
def deliver_analysis():
    """TODO
    - [x] Filter samples, select the ones from the original case
    - [x] Update the sample.delivered_at
    - [x] Call trailblazer to mark the analysis as delivered
    - [ ] Commit changes to  StatusDb if TB call went well, else rollback
    """

    if trailblazer_id := request.args.get("trailblazer_id", type=int):
        # TODO: consider scenario when trailblazer id does not match an analysis
        analysis: Analysis = db.get_analysis_by_trailblazer_id(trailblazer_id)
        case: Case = analysis.case
        for case_sample in case.links:
            # TODO group meditation on attribute name
            if (
                case_sample.is_original
                and not case_sample.sample.delivered_at
                and passes_on_reads(case_sample)
            ):
                case_sample.sample.delivered_at = datetime.now()
        try:
            analysis_client.mark_analyses_as_delivered(trailblazer_ids=[trailblazer_id])
        except TrailblazerAPIHTTPError:
            db.rollback()
            return Response(status=HTTPStatus.BAD_GATEWAY)
        finally:
            db.commit_to_store()
        return Response(status=HTTPStatus.NO_CONTENT)
    else:
        # TODO add test
        # TODO add error message shaming the bad request
        return jsonify({}), HTTPStatus.BAD_REQUEST


def passes_on_reads(case_sample: CaseSample) -> bool:
    if case_sample.case.data_analysis in [Workflow.MICROSALT, Workflow.TAXPROFILER]:
        return case_sample.sample.reads >= case_sample.sample.expected_reads_for_sample
    else:
        return True
