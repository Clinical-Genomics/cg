import logging
from http import HTTPStatus
from typing import Any

from flask import Blueprint, abort, g, jsonify, make_response, request

from cg.exc import (
    CaseNotFoundError,
    OrderMismatchError,
)
from cg.server.dto.delivery_message.delivery_message_request import DeliveryMessageRequest
from cg.server.dto.delivery_message.delivery_message_response import DeliveryMessageResponse
from cg.server.dto.sequencing_metrics.sequencing_metrics_request import SequencingMetricsRequest
from cg.server.endpoints.utils import before_request, is_public
from cg.server.ext import (
    db,
    delivery_message_service,
)
from cg.server.endpoints.utils import before_request, is_public
from cg.server.ext import db, delivery_message_service, lims, order_service, osticket
from cg.server.utils import parse_metrics_into_request
from cg.store.models import (
    Analysis,
    Application,
    ApplicationLimitations,
    Customer,
    IlluminaSampleSequencingMetrics,
    Pool,
    Sample,
)

LOG = logging.getLogger(__name__)
BLUEPRINT = Blueprint("api", __name__, url_prefix="/api/v1")
BLUEPRINT.before_request(before_request)


@BLUEPRINT.route("/samples")
def parse_samples():
    """Return samples."""
    if request.args.get("status") and not g.current_user.is_admin:
        return abort(HTTPStatus.FORBIDDEN)
    if request.args.get("status") == "incoming":
        samples: list[Sample] = db.get_samples_to_receive()
    elif request.args.get("status") == "labprep":
        samples: list[Sample] = db.get_samples_to_prepare()
    elif request.args.get("status") == "sequencing":
        samples: list[Sample] = db.get_samples_to_sequence()
    else:
        customers: list[Customer] | None = (
            None if g.current_user.is_admin else g.current_user.customers
        )
        samples: list[Sample] = db.get_samples_by_customer_id_and_pattern(
            pattern=request.args.get("enquiry"), customers=customers
        )
    limit = int(request.args.get("limit", 50))
    parsed_samples: list[dict] = [sample.to_dict() for sample in samples[:limit]]
    return jsonify(samples=parsed_samples, total=len(samples))


@BLUEPRINT.route("/samples/<sample_id>")
def parse_sample(sample_id):
    """Return a single sample."""
    sample: Sample = db.get_sample_by_internal_id(sample_id)
    if sample is None:
        return abort(HTTPStatus.NOT_FOUND)
    if not g.current_user.is_admin and (sample.customer not in g.current_user.customers):
        return abort(HTTPStatus.FORBIDDEN)
    return jsonify(**sample.to_dict(links=True, flowcells=True))


@BLUEPRINT.route("/samples_in_collaboration/<sample_id>")
def parse_sample_in_collaboration(sample_id):
    """Return a single sample."""
    sample: Sample = db.get_sample_by_internal_id(sample_id)
    customer: Customer = db.get_customer_by_internal_id(
        customer_internal_id=request.args.get("customer")
    )
    if sample.customer not in customer.collaborators:
        return abort(HTTPStatus.FORBIDDEN)
    return jsonify(**sample.to_dict(links=True, flowcells=True))


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
def parse_analyses():
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
def parse_current_user_information():
    """Return information about current user."""
    if not g.current_user.is_admin and not g.current_user.customers:
        LOG.error(
            "%s is not admin and is not connected to any customers, aborting", g.current_user.email
        )
        return abort(HTTPStatus.FORBIDDEN)

    return jsonify(user=g.current_user.to_dict())


@BLUEPRINT.route("/applications")
@is_public
def parse_applications():
    """Return application tags."""
    applications: list[Application] = db.get_applications_is_not_archived()
    parsed_applications: list[dict] = [application.to_dict() for application in applications]
    return jsonify(applications=parsed_applications)


@BLUEPRINT.route("/applications/<tag>")
@is_public
def parse_application(tag: str):
    """Return an application tag."""
    application: Application = db.get_application_by_tag(tag=tag)
    if not application:
        return abort(make_response(jsonify(message="Application not found"), HTTPStatus.NOT_FOUND))

    application_limitations: list[ApplicationLimitations] = db.get_application_limitations_by_tag(
        tag
    )
    application_dict: dict[str, Any] = application.to_dict()
    application_dict["workflow_limitations"] = [
        limitation.to_dict() for limitation in application_limitations
    ]
    return jsonify(**application_dict)


@BLUEPRINT.route("/applications/<tag>/workflow_limitations")
@is_public
def get_application_workflow_limitations(tag: str):
    """Return application workflow specific limitations."""
    if application_limitations := db.get_application_limitations_by_tag(tag):
        return jsonify([limitation.to_dict() for limitation in application_limitations])
    else:
        return jsonify(message="Application limitations not found"), HTTPStatus.NOT_FOUND
