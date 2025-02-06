from flask import Blueprint, jsonify

from cg.server.endpoints.sequencing_metrics.error_handler import handle_endpoint_errors
from cg.server.endpoints.sequencing_run.dtos import PacbioSequencingRunsResponse
from cg.server.endpoints.utils import before_request
from cg.server.ext import db
from cg.store.models import PacbioSequencingRun

PACBIO_SEQUENCING_RUN_BLUEPRINT = Blueprint("pacbio_sequencing_run", __name__, url_prefix="/api/v1")
PACBIO_SEQUENCING_RUN_BLUEPRINT.before_request(before_request)


@PACBIO_SEQUENCING_RUN_BLUEPRINT.route("/pacbio_sequencing_run/<run_name>", methods=["GET"])
@handle_endpoint_errors
def get_sequencing_metrics(run_name: str):
    runs: list[PacbioSequencingRun] = db.get_pacbio_sequencing_runs_by_run_name(run_name)
    response = PacbioSequencingRunsResponse(runs=runs)
    return jsonify(response.model_dump())
