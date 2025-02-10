from flask import Blueprint, jsonify

from cg.server.endpoints.error_handler import handle_missing_entries
from cg.server.endpoints.sequencing_run.dtos import PacbioSequencingRunsResponse
from cg.server.endpoints.utils import before_request
from cg.server.ext import pacbio_sequencing_runs_service

PACBIO_SEQUENCING_RUN_BLUEPRINT = Blueprint(
    "pacbio_sequencing_run", __name__, url_prefix="/api/v1/pacbio_sequencing_run"
)
PACBIO_SEQUENCING_RUN_BLUEPRINT.before_request(before_request)


@PACBIO_SEQUENCING_RUN_BLUEPRINT.route("/<run_name>", methods=["GET"])
@handle_missing_entries
def get_sequencing_runs(run_name: str):
    response: PacbioSequencingRunsResponse = (
        pacbio_sequencing_runs_service.get_sequencing_runs_by_name(run_name)
    )
    return jsonify(response.model_dump())
