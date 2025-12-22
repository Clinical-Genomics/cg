from http import HTTPStatus
from unittest.mock import Mock

from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from cg.server.endpoints.sequencing_run.dtos import (
    PacbioSequencingRunDTO,
    PacbioSequencingRunResponse,
)
from cg.server.ext import pacbio_sequencing_runs_service as sequencing_runs_service


def test_get_pacbio_sequencing_runs(client: FlaskClient):
    # GIVEN two sequencing runs exists
    sequencing_runs_service.get_sequencing_runs = Mock(
        return_value=PacbioSequencingRunResponse(
            pacbio_sequencing_runs=[
                PacbioSequencingRunDTO(
                    run_name="rudolf", comment="This one was crazy!", processed=True
                ),
                PacbioSequencingRunDTO(run_name="santa", comment="Ho, Ho, Ho", processed=False),
            ]
        )
    )

    # WHEN a request is made to get a delivery message for the case
    response: TestResponse = client.get("/api/v1/pacbio_sequencing_runs")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains a message
    assert response.json
    assert response.json["pacbio_sequencing_runs"] == [
        {"run_name": "rudolf", "comment": "This one was crazy!", "processed": True},
        {"run_name": "santa", "comment": "Ho, Ho, Ho", "processed": False},
    ]


def test_get_pacbio_sequencing_runs_with_pagination(client: FlaskClient):

    # WHEN a request is made to get a delivery message for the case
    response: TestResponse = client.get("/api/v1/pacbio_sequencing_runs?page=5&page_size=50")
