from flask import Blueprint, jsonify

from cg.server.endpoints.error_handler import handle_missing_entries
from cg.server.endpoints.sequencing_run.dtos import (
    PacbioSequencingRunResponse,
    PacbioSmrtCellMetricsResponse,
)
from cg.server.endpoints.utils import before_request
from cg.server.ext import pacbio_sequencing_runs_service

PACBIO_SEQUENCING_RUN_BLUEPRINT = Blueprint(
    "pacbio_sequencing_run", __name__, url_prefix="/api/v1/pacbio_sequencing_run"
)
PACBIO_SEQUENCING_RUNS_BLUEPRINT = Blueprint(
    "pacbio_sequencing_runs", __name__, url_prefix="/api/v1/"
)
PACBIO_SEQUENCING_RUN_BLUEPRINT.before_request(before_request)
PACBIO_SEQUENCING_RUNS_BLUEPRINT.before_request(before_request)


@PACBIO_SEQUENCING_RUN_BLUEPRINT.route("/<run_name>", methods=["GET"])
@handle_missing_entries
def get_sequencing_runs(run_name: str):
    response: PacbioSmrtCellMetricsResponse = (
        pacbio_sequencing_runs_service.get_sequencing_runs_by_name(run_name)
    )
    return jsonify(response.model_dump())


@PACBIO_SEQUENCING_RUNS_BLUEPRINT.route("/pacbio_sequencing_runs", methods=["GET"])
@handle_missing_entries
def get_sequencing_runs_new():  # TODO rename endpoint to pacbio_sequencing_runs
    sequencing_runs: PacbioSequencingRunResponse = (
        pacbio_sequencing_runs_service.get_sequencing_runs()
    )
    return jsonify(sequencing_runs.model_dump())
