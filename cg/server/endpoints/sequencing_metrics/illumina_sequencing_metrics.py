from flask import Blueprint, jsonify

from cg.server.endpoints.sequencing_metrics.error_handler import handle_endpoint_errors
from cg.server.endpoints.utils import before_request
from cg.server.ext import sample_run_metrics_service
from cg.services.sample_run_metrics_service.dtos import IlluminaSequencingMetricsDTO

FLOW_CELLS_BLUEPRINT = Blueprint("flowcells", __name__, url_prefix="/api/v1")
FLOW_CELLS_BLUEPRINT.before_request(before_request)


@FLOW_CELLS_BLUEPRINT.route("/flowcells/<flow_cell_name>/sequencing_metrics", methods=["GET"])
@handle_endpoint_errors
def get_sequencing_metrics(flow_cell_name: str):
    metrics: list[IlluminaSequencingMetricsDTO] = sample_run_metrics_service.get_illumina_metrics(
        flow_cell_name
    )
    return jsonify([metric.model_dump() for metric in metrics])
