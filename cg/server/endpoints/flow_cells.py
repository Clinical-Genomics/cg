from flask import Blueprint, jsonify

from cg.server.endpoints.utils import before_request
from cg.server.ext import flow_cell_service

FLOW_CELLS_BLUEPRINT = Blueprint("flowcells", __name__, url_prefix="/api/v1")
FLOW_CELLS_BLUEPRINT.before_request(before_request)


@FLOW_CELLS_BLUEPRINT.route("/flowcells/<flow_cell_name>/sequencing_metrics", methods=["GET"])
def get_sequencing_metrics(flow_cell_name: str):
    metrics = flow_cell_service.get_metrics(flow_cell_name)
    return jsonify([metric.model_dump() for metric in metrics])
