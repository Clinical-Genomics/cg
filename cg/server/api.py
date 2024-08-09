import logging
from http import HTTPStatus

from flask import Blueprint, abort, g, jsonify, request

from cg.server.dto.sequencing_metrics.sequencing_metrics_request import SequencingMetricsRequest
from cg.server.endpoints.utils import before_request
from cg.server.ext import db
from cg.server.endpoints.utils import before_request
from cg.server.ext import db
from cg.server.utils import parse_metrics_into_request
from cg.store.models import (
    Analysis,
    Customer,
    IlluminaSampleSequencingMetrics,
    Pool,
)

LOG = logging.getLogger(__name__)
BLUEPRINT = Blueprint("api", __name__, url_prefix="/api/v1")
BLUEPRINT.before_request(before_request)


@BLUEPRINT.route("/pools")
def parse_pools():
    """Return pools."""
    customers: list[Customer] | None = (
        g.current_user.customers if not g.current_user.is_admin else None
    )
    pools: list[Pool] = db.get_pools_to_render(
        customers=customers, enquiry=request.args.get("enquiry")
    )
    parsed_pools: list[dict] = [pool_obj.to_dict() for pool_obj in pools[:30]]
    return jsonify(pools=parsed_pools, total=len(pools))


@BLUEPRINT.route("/pools/<pool_id>")
def parse_pool(pool_id):
    """Return a single pool."""
    pool: Pool = db.get_pool_by_entry_id(entry_id=pool_id)
    if pool is None:
        return abort(HTTPStatus.NOT_FOUND)
    if not g.current_user.is_admin and (pool.customer not in g.current_user.customers):
        return abort(HTTPStatus.FORBIDDEN)
    return jsonify(**pool.to_dict())


@BLUEPRINT.route("/flowcells/<flow_cell_name>/sequencing_metrics", methods=["GET"])
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


@BLUEPRINT.route("/analyses")
def get_analyses():
    """Return analyses."""
    if request.args.get("status") == "delivery":
        analyses: list[Analysis] = db.get_analyses_to_deliver_for_pipeline()
    elif request.args.get("status") == "upload":
        analyses: list[Analysis] = db.get_analyses_to_upload()
    else:
        analyses: list[Analysis] = db.get_analyses()
    parsed_analysis: list[dict] = [analysis_obj.to_dict() for analysis_obj in analyses[:30]]
    return jsonify(analyses=parsed_analysis, total=len(analyses))


@BLUEPRINT.route("/me")
def get_user_information():
    """Return information about current user."""
    if not g.current_user.is_admin and not g.current_user.customers:
        LOG.error(
            "%s is not admin and is not connected to any customers, aborting", g.current_user.email
        )
        return abort(HTTPStatus.FORBIDDEN)

    return jsonify(user=g.current_user.to_dict())
