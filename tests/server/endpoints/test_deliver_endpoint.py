from datetime import datetime
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
    pre_time = datetime.now()
    sample_3: Sample = create_autospec(Sample, delivered_at=pre_time)

    # GIVEN a case to be delivered
    case: Case = create_autospec(Case, samples=[sample_1, sample_2])

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

    # THEN the sample should have been delivered
    assert sample_1.delivered_at is not None
    assert sample_2.delivered_at is not None

    # THEN endpoint in Trailblazer was called
    analysis_client.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )
