from http import HTTPStatus
from flask.testing import FlaskClient

from cg.store.models import Case


def test_get_delivery_message(client: FlaskClient, case: Case):
    # GIVEN a case

    # WHEN a request is made to get a delivery message for the case
    response = client.get(f"/api/v1/cases/{case.internal_id}/delivery_message")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains a message
    assert response.json["message"]
