from datetime import datetime, timedelta
from http import HTTPStatus
from unittest.mock import Mock, create_autospec

from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from cg.server.endpoints import deliver
from cg.server.ext import AnalysisClient, FlaskStore
from cg.store.models import Analysis, Case, Sample


def test_deliver_trailblazer_analysis(client: FlaskClient, mocker: MockerFixture):
    # GIVEN a trailblazer analysis id
    trailblazer_id = 666666

    # GIVEN samples that should be delivered
    sample_1: Sample = create_autospec(Sample, delivered_at=None)
    sample_2: Sample = create_autospec(Sample, delivered_at=None)

    # GIVEN a sample that is already delivered
    yesterday = datetime.now() - timedelta(days=1)
    sample_3: Sample = create_autospec(Sample, delivered_at=yesterday)

    # GIVEN a sample orinating from a different case

    # GIVEN a case to be delivered
    case: Case = create_autospec(Case, samples=[sample_1, sample_2, sample_3])

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # GIVEN a store
    status_db: FlaskStore = create_autospec(FlaskStore)
    status_db.get_analysis_by_trailblazer_id = Mock(return_value=analysis)
    mocker.patch.object(deliver, "db", status_db)

    # GIVEN a TrailblazerAPI
    analysis_client = create_autospec(AnalysisClient)
    mocker.patch.object(deliver, "analysis_client", analysis_client)

    # WHEN calling the endpoint
    response = client.post(f"/api/v1/deliver?trailblazer_id={trailblazer_id}")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the samples should have been delivered
    assert sample_1.delivered_at is not None
    assert sample_2.delivered_at is not None

    # THEN the delivered sample should have the same delivered timestamp as before
    assert sample_3.delivered_at == yesterday

    # THEN endpoint in Trailblazer was called
    analysis_client.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )
