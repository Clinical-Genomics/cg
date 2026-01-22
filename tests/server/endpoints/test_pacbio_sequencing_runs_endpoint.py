from http import HTTPStatus
from unittest.mock import Mock

from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from cg.server.endpoints.sequencing_run.dtos import (
    PacbioSequencingRunDTO,
    PacbioSequencingRunResponse,
    PacbioSequencingRunUpdateRequest,
)
from cg.server.ext import pacbio_sequencing_runs_service as sequencing_runs_service


def test_get_pacbio_sequencing_runs(client: FlaskClient):
    # GIVEN two sequencing runs exists
    sequencing_runs_service.get_sequencing_runs = Mock(
        return_value=PacbioSequencingRunResponse(
            pacbio_sequencing_runs=[
                PacbioSequencingRunDTO(
                    id=9, internal_id="rudolf", comment="This one was crazy!", processed=True
                ),
                PacbioSequencingRunDTO(
                    id=1, internal_id="santa", comment="Ho, Ho, Ho", processed=False
                ),
            ],
            total_count=2,
        )
    )

    # WHEN a request is made to get a delivery message for the case
    response: TestResponse = client.get("/api/v1/pacbio_sequencing_runs")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains a message
    assert response.json
    assert response.json["total_count"] == 2
    assert response.json["pacbio_sequencing_runs"] == [
        {"id": 9, "internal_id": "rudolf", "comment": "This one was crazy!", "processed": True},
        {"id": 1, "internal_id": "santa", "comment": "Ho, Ho, Ho", "processed": False},
    ]


def test_get_pacbio_sequencing_runs_with_pagination(client: FlaskClient):
    # GIVEN a sequencing run service
    sequencing_runs_service.get_sequencing_runs = Mock(
        return_value=PacbioSequencingRunResponse(pacbio_sequencing_runs=[], total_count=0)
    )

    # WHEN a request is made to get a delivery message for the case
    client.get("/api/v1/pacbio_sequencing_runs?page=5&pageSize=50")

    # THEN the page number and the page size should be passed
    sequencing_runs_service.get_sequencing_runs.assert_called_once_with(page=5, page_size=50)


def test_patch_pacbio_sequencing_runs_successful(client: FlaskClient):
    # GIVEN a pacbio sequencing run update request
    sequencing_runs_service.update_sequencing_run = Mock()
    body = {"comment": "This is a comment", "processed": True}

    # WHEN a request is made to update a pacbio sequencing run
    response = client.patch("/api/v1/pacbio_sequencing_runs/1", json=body)

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.NO_CONTENT

    # THEN the sequencing run service should be called with the update request
    sequencing_runs_service.update_sequencing_run.assert_called_once_with(
        update_request=PacbioSequencingRunUpdateRequest(id=1, **body)
    )


def test_patch_pacbio_sequencing_runs_malformed_processed_value(client: FlaskClient):
    # GIVEN a pacbio sequencing run update request with a malformed processed value
    sequencing_runs_service.update_sequencing_run = Mock()
    body = {"processed": "Santa Claus"}

    # WHEN a request is made to update a pacbio sequencing run
    response = client.patch("/api/v1/pacbio_sequencing_runs/1", json=body)

    # THEN the response should not be successful
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    # THEN the sequencing run service should not be called with the update request
    sequencing_runs_service.update_sequencing_run.assert_not_called()


def test_patch_pacbio_sequencing_runs_internal_server_error(client: FlaskClient):
    # GIVEN that there is an error in the sequencing run service
    sequencing_runs_service.update_sequencing_run = Mock(side_effect=Exception("No gifts for you!"))
    body = {"processed": True}

    # WHEN a request is made to update a pacbio sequencing run
    response = client.patch("/api/v1/pacbio_sequencing_runs/1", json=body)

    # THEN the response should not be successful
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    # THEN the sequencing run service should be called with the update request
    sequencing_runs_service.update_sequencing_run.assert_called_once_with(
        update_request=PacbioSequencingRunUpdateRequest(id=1, **body)
    )
