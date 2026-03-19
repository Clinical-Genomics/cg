from http import HTTPStatus
from unittest.mock import Mock, create_autospec

import pytest
from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from cg.exc import AnalysisDoesNotExistError, TrailblazerAPIHTTPError
from cg.server.endpoints import deliver
from cg.server.ext import FlaskStore, mark_as_delivered_service
from cg.store.models import Analysis
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.fixture
def status_db(mocker: MockerFixture) -> TypedMock[FlaskStore]:
    status_db: TypedMock[FlaskStore] = create_typed_mock(FlaskStore)
    mocker.patch.object(deliver, "db", status_db.as_type)
    return status_db


def test_deliver_trailblazer_analyses(
    client: FlaskClient, status_db: TypedMock[FlaskStore], mocker: MockerFixture
):
    # GIVEN two trailblazer analysis ids
    trailblazer_id_1 = 666666
    trailblazer_id_2 = 555555

    # GIVEN an analysis linked to the trailblazer analysis
    analysis_1: Analysis = create_autospec(Analysis, trailblazer_id=trailblazer_id_1)
    analysis_2: Analysis = create_autospec(Analysis, trailblazer_id=trailblazer_id_2)
    status_db.as_type.get_analysis_by_trailblazer_id = lambda trailblazer_id: (
        analysis_1 if trailblazer_id == trailblazer_id_1 else analysis_2
    )

    # GIVEN a service to mark the analysis as delivered
    mark_analysis_mock = mocker.patch.object(mark_as_delivered_service, "mark_analyses")

    # WHEN calling the endpoint
    response = client.post(
        path="/api/v1/deliver", json={"trailblazer_ids": [trailblazer_id_1, trailblazer_id_2]}
    )

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.NO_CONTENT

    # THEN the analysis was marked as delivered
    mark_analysis_mock.assert_called_once_with([analysis_1, analysis_2])

    # THEN these changes were committed to the database
    status_db.as_mock.commit_to_store.assert_called_once()


def test_deliver_trailblazer_analyses_client_error(client: FlaskClient, mocker: MockerFixture):
    # GIVEN a trailblazer analysis id
    trailblazer_id = 666666

    # GIVEN a store
    status_db: TypedMock[FlaskStore] = create_typed_mock(FlaskStore)
    mocker.patch.object(deliver, "db", status_db.as_type)

    # GIVEN a service that marks the analysis as delivered that fails when calling Trailblazer
    mocker.patch.object(
        mark_as_delivered_service, "mark_analyses", side_effect=TrailblazerAPIHTTPError
    )

    # WHEN calling the endpoint
    response = client.post(path="/api/v1/deliver", json={"trailblazer_ids": [trailblazer_id]})

    # THEN the response should be bad gateway
    assert response.status_code == HTTPStatus.BAD_GATEWAY

    # THEN the database changes were rolled back
    status_db.as_mock.rollback.assert_called_once()


def test_no_trailblazer_ids_given(client: FlaskClient):
    # WHEN calling the endpoint without Trailblazer ids
    response = client.post("/api/v1/deliver")

    # THEN the response is unsupported media type
    assert response.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE


def test_trailblazer_id_not_found_in_database(
    client: FlaskClient, status_db: TypedMock[FlaskStore]
):
    # GIVEN a trailblazer analysis id
    trailblazer_id = 666666

    # GIVEN that the trailblazer id has no matching analysis
    status_db.as_type.get_analysis_by_trailblazer_id = Mock(side_effect=AnalysisDoesNotExistError)

    # WHEN calling the endpoint
    response = client.post(path="/api/v1/deliver", json={"trailblazer_ids": [trailblazer_id]})

    # THEN the response should be a bad request
    assert response.status_code == HTTPStatus.BAD_REQUEST
