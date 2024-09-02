import logging
from http import HTTPStatus
from flask import Blueprint, jsonify

from cg.server.dto.sequencing_metrics.sequencing_metrics_request import SequencingMetricsRequest
from cg.server.ext import db
from cg.server.endpoints.utils import before_request
from cg.server.utils import parse_metrics_into_request
from cg.store.models import IlluminaSampleSequencingMetrics

FLOW_CELLS_BLUEPRINT = Blueprint("flowcells", __name__, url_prefix="/api/v1")
FLOW_CELLS_BLUEPRINT.before_request(before_request)


@FLOW_CELLS_BLUEPRINT.route("/flowcells/<flow_cell_name>/sequencing_metrics", methods=["GET"])
def get_sequencing_metrics(flow_cell_name: str):
    """Return sample lane sequencing metrics for a flow cell."""
    if not flow_cell_name:
        return jsonify({"error": "Invalid or missing flow cell id"}), HTTPStatus.BAD_REQUEST
    sequencing_metrics: list[IlluminaSampleSequencingMetrics] = (
        db.get_illumina_sequencing_run_by_device_internal_id(flow_cell_name).sample_metrics
    )
    if not sequencing_metrics:
        return (
            jsonify({"error": f"Sequencing metrics not found for flow cell {flow_cell_name}."}),
            HTTPStatus.NOT_FOUND,
        )
    metrics_dtos: list[SequencingMetricsRequest] = parse_metrics_into_request(sequencing_metrics)
    return jsonify([metric.model_dump() for metric in metrics_dtos])
