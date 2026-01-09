from http import HTTPStatus

from flask import Blueprint, Response, jsonify, request
from pydantic import ValidationError

from cg.server.endpoints.error_handler import handle_missing_entries
from cg.server.endpoints.sequencing_run.dtos import (
    PacbioSequencingRunResponse,
    PacbioSequencingRunUpdateRequest,
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
    page: int = int(request.args.get("page", "0"))
    page_size: int = int(request.args.get("pageSize", "0"))
    sequencing_runs: PacbioSequencingRunResponse = (
        pacbio_sequencing_runs_service.get_sequencing_runs(page=page, page_size=page_size)
    )
    return jsonify(sequencing_runs.model_dump())


@PACBIO_SEQUENCING_RUNS_BLUEPRINT.route("/pacbio_sequencing_runs/<id>", methods=["PATCH"])
@handle_missing_entries
def update_sequencing_run(id: str):
    try:
        update_request = PacbioSequencingRunUpdateRequest(id=id, **request.json)
    except ValidationError:
        return Response(status=HTTPStatus.UNPROCESSABLE_ENTITY)
    pacbio_sequencing_runs_service.update_sequencing_run(update_request=update_request)
    return Response(status=HTTPStatus.NO_CONTENT)
