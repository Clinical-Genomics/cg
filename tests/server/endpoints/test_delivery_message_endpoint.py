from http import HTTPStatus
from flask.testing import FlaskClient


def test_get_delivery_message(client: FlaskClient, case_id: str):
     # GIVEN a case id

    # WHEN a request is made to get a delivery message for the case
    response = client.get(f"/api/v1/cases/{case_id}/delivery_message")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains a message
    assert response.json["message"]
