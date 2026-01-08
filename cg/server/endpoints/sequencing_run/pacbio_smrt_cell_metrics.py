from flask import Blueprint, jsonify

from cg.server.endpoints.error_handler import handle_missing_entries
from cg.server.endpoints.sequencing_run.dtos import PacbioSmrtCellMetricsResponse
from cg.server.endpoints.utils import before_request
from cg.server.ext import pacbio_sequencing_runs_service

PACBIO_SMRT_CELL_METRICS_BLUEPRINT = Blueprint(
    "pacbio_smrt_cell_metrics", __name__, url_prefix="/api/v1/pacbio_smrt_cell_metrics"
)
PACBIO_SMRT_CELL_METRICS_BLUEPRINT.before_request(before_request)


@PACBIO_SMRT_CELL_METRICS_BLUEPRINT.route("/<run_name>", methods=["GET"])
@handle_missing_entries
def get_smrt_cell_metrics(run_name: str):
    response: PacbioSmrtCellMetricsResponse = (
        pacbio_sequencing_runs_service.get_sequencing_runs_by_name(run_name)
    )
    return jsonify(response.model_dump())
