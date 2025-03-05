from flask import Blueprint, jsonify, request

from cg.server.endpoints.sequencing_metrics.dtos import (
    PacbioSequencingMetricsRequest,
    PacbioSequencingMetricsResponse,
)
from cg.server.endpoints.sequencing_metrics.error_handler import handle_endpoint_errors
from cg.server.endpoints.utils import before_request
from cg.server.ext import sample_run_metrics_service
from cg.services.sample_run_metrics_service.dtos import PacbioSequencingMetricsDTO

PACBIO_SAMPLE_SEQUENCING_METRICS_BLUEPRINT = Blueprint(
    "pacbio_sample_sequencing_metrics", __name__, url_prefix="/api/v1"
)
PACBIO_SAMPLE_SEQUENCING_METRICS_BLUEPRINT.before_request(before_request)


@PACBIO_SAMPLE_SEQUENCING_METRICS_BLUEPRINT.route("/pacbio_sample_sequencing_metrics")
@handle_endpoint_errors
def get_sequencing_metrics():
    sequencing_metrics_request = PacbioSequencingMetricsRequest(
        sample_id=request.args.get("sample_id"), smrt_cell_ids=request.args.getlist("smrt_cell_ids")
    )
    metrics: list[PacbioSequencingMetricsDTO] = sample_run_metrics_service.get_pacbio_metrics(
        sequencing_metrics_request
    )
    response = PacbioSequencingMetricsResponse(metrics=metrics)
    return jsonify(response.model_dump())
