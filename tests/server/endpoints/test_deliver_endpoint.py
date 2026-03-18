from datetime import datetime, timedelta
from http import HTTPStatus
from unittest.mock import Mock, create_autospec

import pytest
from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from cg.constants import Workflow
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
    status_db.as_type.get_analysis_by_trailblazer_id = Mock(return_value=analysis)

    # GIVEN a TrailblazerAPI
    analysis_client = create_autospec(AnalysisClient)
    mocker.patch.object(mark_as_delivered_service, "trailblazer_api", analysis_client)

    mocker.patch.object(mark_as_delivered_service, "status_db", status_db.as_type)

    # WHEN calling the endpoint
    response = client.post(f"/api/v1/deliver?trailblazer_id={trailblazer_id}")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.NO_CONTENT

    # THEN the samples should have been delivered
    assert sample_1.delivered_at is not None
    assert sample_2.delivered_at is not None

    # THEN endpoint in Trailblazer was called
    analysis_client.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )

    # THEN these changes were commited to the database
    status_db.as_mock.commit_to_store.assert_called_once()


def test_deliver_mix_original_non_original_samples(client: FlaskClient, mocker: MockerFixture):
    # GIVEN a trailblazer analysis id
    trailblazer_id = 666666

    # GIVEN a new sample and an existing sample
    sample_new: Sample = create_autospec(Sample, delivered_at=None)
    sample_existing: Sample = create_autospec(Sample, delivered_at=None)

    # GIVEN a case with the two samples
    case: Case = create_autospec(Case)

    case_sample_new = create_autospec(CaseSample, case=case, sample=sample_new, is_original=True)
    case_sample_existing = create_autospec(
        CaseSample, case=case, sample=sample_existing, is_original=False
    )
    case.links = [case_sample_new, case_sample_existing]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # GIVEN a store
    status_db: FlaskStore = create_autospec(FlaskStore)
    status_db.get_analysis_by_trailblazer_id = Mock(return_value=analysis)
    mocker.patch.object(deliver, "db", status_db)

    mocker.patch.object(mark_as_delivered_service, "status_db", status_db)

    # GIVEN a TrailblazerAPI
    analysis_client = create_autospec(AnalysisClient)
    mocker.patch.object(mark_as_delivered_service, "trailblazer_api", analysis_client)

    # WHEN calling the endpoint
    response = client.post(f"/api/v1/deliver?trailblazer_id={trailblazer_id}")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.NO_CONTENT

    # THEN only the new sample should be delivered
    assert sample_new.delivered_at is not None
    assert sample_existing.delivered_at is None

    # THEN endpoint in Trailblazer was called
    analysis_client.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )


def test_deliver_rerun_case(client: FlaskClient, mocker: MockerFixture):
    # GIVEN a trailblazer analysis id
    trailblazer_id = 666666

    # GIVEN two already delivered samples
    yesterday = datetime.now() - timedelta(days=1)
    sample_1: Sample = create_autospec(Sample, delivered_at=yesterday)
    sample_2: Sample = create_autospec(Sample, delivered_at=yesterday)

    # GIVEN a case with the two samples
    case: Case = create_autospec(Case)
    case_sample_1 = create_autospec(CaseSample, case=case, sample=sample_1, is_original=True)
    case_sample_2 = create_autospec(CaseSample, case=case, sample=sample_2, is_original=False)
    case.links = [case_sample_1, case_sample_2]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # GIVEN a store
    status_db: FlaskStore = create_autospec(FlaskStore)
    status_db.get_analysis_by_trailblazer_id = Mock(return_value=analysis)
    mocker.patch.object(deliver, "db", status_db)

    mocker.patch.object(mark_as_delivered_service, "status_db", status_db)

    # GIVEN a TrailblazerAPI
    analysis_client = create_autospec(AnalysisClient)
    mocker.patch.object(mark_as_delivered_service, "trailblazer_api", analysis_client)

    # WHEN calling the endpoint
    response = client.post(f"/api/v1/deliver?trailblazer_id={trailblazer_id}")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.NO_CONTENT

    # THEN the delivered_at for both samples should be untouched
    assert sample_1.delivered_at is yesterday
    assert sample_2.delivered_at is yesterday

    # THEN endpoint in Trailblazer was called
    analysis_client.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )


def test_mixed_delivered_at_original_samples(client: FlaskClient, mocker: MockerFixture):
    # GIVEN a trailblazer analysis id
    trailblazer_id = 666666

    # GIVEN one delivered sample and one undelivered sample
    yesterday = datetime.now() - timedelta(days=1)
    sample_1: Sample = create_autospec(Sample, delivered_at=yesterday)
    sample_2: Sample = create_autospec(Sample, delivered_at=None)

    # GIVEN that the two samples originally belong to this given case
    case: Case = create_autospec(Case, samples=[sample_1, sample_2])
    case_sample_1 = create_autospec(CaseSample, case=case, sample=sample_1, is_original=True)
    case_sample_2 = create_autospec(CaseSample, case=case, sample=sample_2, is_original=True)
    case.links = [case_sample_1, case_sample_2]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # GIVEN a store
    status_db: FlaskStore = create_autospec(FlaskStore)
    status_db.get_analysis_by_trailblazer_id = Mock(return_value=analysis)
    mocker.patch.object(deliver, "db", status_db)

    mocker.patch.object(mark_as_delivered_service, "status_db", status_db)

    # GIVEN a TrailblazerAPI
    analysis_client = create_autospec(AnalysisClient)
    mocker.patch.object(mark_as_delivered_service, "trailblazer_api", analysis_client)

    # WHEN calling the endpoint
    response = client.post(f"/api/v1/deliver?trailblazer_id={trailblazer_id}")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.NO_CONTENT

    # THEN only the delivered_at of the undelivered sample is updated
    assert sample_1.delivered_at is yesterday
    assert sample_2.delivered_at is not None

    # THEN endpoint in Trailblazer was called
    analysis_client.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )


def test_partial_delivery(client: FlaskClient, mocker: MockerFixture):
    # GIVEN a trailblazer analysis id
    trailblazer_id = 666666

    # GIVEN one delivered sample and one undelivered sample
    sample_enough_reads: Sample = create_autospec(
        Sample, delivered_at=None, expected_reads_for_sample=10, reads=11
    )
    sample_not_enough_reads: Sample = create_autospec(
        Sample, delivered_at=None, expected_reads_for_sample=10, reads=9
    )

    # GIVEN that the two samples originally belong to this given case
    case: Case = create_autospec(Case, data_analysis=Workflow.TAXPROFILER)
    case_sample_enough_reads = create_autospec(
        CaseSample, case=case, sample=sample_enough_reads, is_original=True
    )
    case_sample_not_enough_reads = create_autospec(
        CaseSample, case=case, sample=sample_not_enough_reads, is_original=True
    )
    case.links = [case_sample_enough_reads, case_sample_not_enough_reads]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # GIVEN a store
    status_db: FlaskStore = create_autospec(FlaskStore)
    status_db.get_analysis_by_trailblazer_id = Mock(return_value=analysis)
    mocker.patch.object(deliver, "db", status_db)

    mocker.patch.object(mark_as_delivered_service, "status_db", status_db)

    # GIVEN a TrailblazerAPI
    analysis_client = create_autospec(AnalysisClient)
    mocker.patch.object(mark_as_delivered_service, "trailblazer_api", analysis_client)

    # WHEN calling the endpoint
    response = client.post(f"/api/v1/deliver?trailblazer_id={trailblazer_id}")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.NO_CONTENT

    # THEN only the delivered_at of the sample with enough reads is updated
    assert sample_enough_reads.delivered_at is not None
    assert sample_not_enough_reads.delivered_at is None

    # THEN endpoint in Trailblazer was called
    analysis_client.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )


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
