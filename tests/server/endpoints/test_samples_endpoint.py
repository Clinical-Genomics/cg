from http import HTTPStatus

from flask.testing import FlaskClient


def test_update_samples(client: FlaskClient):
    # GIVEN a request body with two sample internal ids and a lims status
    request_body = {
        "samples": [
            {"internal_id": "sample_1", "lims_status": "top-up"},
            {"internal_id": "sample_2", "lims_status": "re-prep"},
        ]
    }

    # WHEN calling the endpoint to update the lims statuses of the samples
    response = client.patch(
        path="/api/v1/samples",
        json=request_body,
    )

    # THEN the samples were updated in the database
    assert response.status_code == HTTPStatus.OK
