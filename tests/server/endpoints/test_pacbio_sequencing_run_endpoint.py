from http import HTTPStatus

from flask.testing import FlaskClient
from werkzeug.test import TestResponse


def test_get_pacbio_sequencing_runs(client: FlaskClient):
    # GIVEN two sequencing runs exists

    # WHEN a request is made to get a delivery message for the case
    response: TestResponse = client.get(f"/api/v1/pacbio_sequencing_run")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains a message
    assert response.json
    assert response.json["message"]
