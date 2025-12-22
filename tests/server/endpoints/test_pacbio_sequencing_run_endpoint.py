from http import HTTPStatus
from unittest.mock import Mock, create_autospec

from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from cg.server.ext import pacbio_sequencing_runs_service as pacbio_global_service
from cg.store.models import PacbioSequencingRun


def test_get_pacbio_sequencing_runs(client: FlaskClient):
    # GIVEN two sequencing runs exists
    pacbio_global_service.get_all_sequencing_runs = Mock(
        return_value=[create_autospec(PacbioSequencingRun), create_autospec(PacbioSequencingRun)]
    )

    # WHEN a request is made to get a delivery message for the case
    response: TestResponse = client.get("/api/v1/pacbio_sequencing_runs")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains a message
    assert response.json
    assert response.json["pacbio_sequencing_runs"] == [
        {"run_name": "rudolf", "comments": "This one was crazy!", "processed": True},
        {"run_name": "santa", "comments": "Ho, Ho, Ho", "processed": False},
    ]
