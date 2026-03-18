from http import HTTPStatus
from unittest.mock import Mock, create_autospec

import pytest
from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from cg.exc import AnalysisDoesNotExistError, TrailblazerAPIHTTPError
from cg.server.endpoints import deliver
from cg.server.ext import AnalysisClient, FlaskStore, mark_as_delivered_service
from cg.store.models import Analysis, Case, CaseSample, Sample
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.fixture
def status_db(mocker: MockerFixture) -> TypedMock[FlaskStore]:
    status_db: TypedMock[FlaskStore] = create_typed_mock(FlaskStore)
    mocker.patch.object(deliver, "db", status_db.as_type)
    return status_db


def test_deliver_trailblazer_analysis(
    client: FlaskClient, status_db: TypedMock[FlaskStore], mocker: MockerFixture
):
    # GIVEN a trailblazer analysis id
    trailblazer_id = 666666

    # GIVEN an analysis linked to the trailblazer analysis
    analysis: Analysis = create_autospec(Analysis, trailblazer_id=trailblazer_id)
    status_db.as_type.get_analysis_by_trailblazer_id = Mock(return_value=analysis)

    # GIVEN a service to mark the analysis as delivered
    mark_analysis_spy = mocker.spy(mark_as_delivered_service, "mark_analysis")

    # WHEN calling the endpoint
    response = client.post(f"/api/v1/deliver?trailblazer_id={trailblazer_id}")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.NO_CONTENT

    # THEN the analysis was marked as delivered
    mark_analysis_spy.assert_called_once_with(analysis)

    # THEN these changes were committed to the database
    status_db.as_mock.commit_to_store.assert_called_once()


def test_deliver_trailblazer_analysis_client_error(client: FlaskClient, mocker: MockerFixture):
    # GIVEN a trailblazer analysis id
    trailblazer_id = 666666

    # GIVEN samples that should be delivered
    sample_1: Sample = create_autospec(Sample, delivered_at=None)
    sample_2: Sample = create_autospec(Sample, delivered_at=None)

    # GIVEN a case to be delivered
    case: Case = create_autospec(Case)
    case_sample_1 = create_autospec(CaseSample, case=case, sample=sample_1, is_original=True)
    case_sample_2 = create_autospec(CaseSample, case=case, sample=sample_2, is_original=True)
    case.links = [case_sample_1, case_sample_2]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # GIVEN a store
    status_db: TypedMock[FlaskStore] = create_typed_mock(FlaskStore)
    status_db.as_type.get_analysis_by_trailblazer_id = Mock(return_value=analysis)
    mocker.patch.object(deliver, "db", status_db.as_type)

    # GIVEN a TrailblazerAPI
    analysis_client = create_autospec(AnalysisClient)
    analysis_client.mark_analyses_as_delivered = Mock(side_effect=TrailblazerAPIHTTPError)
    mocker.patch.object(mark_as_delivered_service, "trailblazer_api", analysis_client)

    mocker.patch.object(mark_as_delivered_service, "status_db", status_db.as_type)

    # WHEN calling the endpoint
    response = client.post(f"/api/v1/deliver?trailblazer_id={trailblazer_id}")

    # THEN the response should be bad gateway
    assert response.status_code == HTTPStatus.BAD_GATEWAY

    # THEN endpoint in Trailblazer was called
    analysis_client.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )

    # THEN the database changes were rolled back
    status_db.as_mock.rollback.assert_called_once()


def test_no_trailblazer_id_given(client: FlaskClient):
    # WHEN calling the endpoint without a trailblazer id
    response = client.post(f"/api/v1/deliver")

    # THEN the response is a bad request
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_trailblazer_id_not_found_in_database(
    client: FlaskClient, status_db: TypedMock[FlaskStore]
):
    # GIVEN a trailblazer analysis id
    trailblazer_id = 666666

    # GIVEN that the trailblazer id has no matching analysis
    status_db.as_type.get_analysis_by_trailblazer_id = Mock(side_effect=AnalysisDoesNotExistError)

    # WHEN calling the endpoint
    response = client.post(f"/api/v1/deliver?trailblazer_id={trailblazer_id}")

    # THEN the response should be a bad request
    assert response.status_code == HTTPStatus.BAD_REQUEST
