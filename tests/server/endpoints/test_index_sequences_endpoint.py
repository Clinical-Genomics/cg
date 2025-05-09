from http import HTTPStatus

from flask.testing import FlaskClient

from cg.services.orders.validation.index_sequences import INDEX_SEQUENCES


def test_get_index_sequences(client: FlaskClient):
    """Tests that index sequence endpoint gives a response"""

    # WHEN a request is made to get index sequences
    endpoint: str = "/api/v1/index_sequences"
    response = client.get(endpoint)

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK
    assert response.json == INDEX_SEQUENCES
