from http import HTTPStatus
from unittest.mock import create_autospec

from flask.testing import FlaskClient

from cg.store.models import Analysis, Case, Sample


def test_deliver_trailblazer_analysis(client: FlaskClient):
    # GIVEN a trailblazer analysis id
    trailblazer_id = 666666

    # GIVEN samples that should be delivered
    sample_1: Sample = create_autospec(Sample, delivered_at=None)
    sample_2: Sample = create_autospec(Sample, delivered_at=None)

    # GIVEN a case to be delivered
    case: Case = create_autospec(Case, samples=[sample_1, sample_2])

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # WHEN calling the endpoint
    response = client.post(f"/api/v1/deliver?trailblazer_id={trailblazer_id}")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the sample should have been delivered
    assert sample_1.delivered_at is not None
    assert sample_2.delivered_at is not None

    # THEN endpoint in trailblazer was called
