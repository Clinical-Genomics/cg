from datetime import datetime
from http import HTTPStatus
from unittest.mock import Mock, call, create_autospec

from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.constants.lims import LimsStatus
from cg.exc import SampleNotFoundError
from cg.server.endpoints import samples
from cg.store.models import Customer, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_update_samples(client: FlaskClient, mocker: MockerFixture):
    # GIVEN a store
    status_db: TypedMock[Store] = create_typed_mock(Store)
    mocker.patch.object(samples, "db", status_db.as_type)

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

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.NO_CONTENT

    # THEN the samples were updated in the database
    status_db.as_mock.update_sample_lims_status.assert_has_calls(
        [
            call(internal_id="sample_1", lims_status=LimsStatus.TOP_UP),
            call(internal_id="sample_2", lims_status=LimsStatus.RE_PREP),
        ]
    )
    status_db.as_mock.commit_to_store.assert_called_once()


def test_update_samples_sample_not_found(client: FlaskClient, mocker: MockerFixture):
    # GIVEN a store that raises an error when trying to get a sample
    status_db: TypedMock[Store] = create_typed_mock(Store)
    status_db.as_type.update_sample_lims_status = Mock(side_effect=SampleNotFoundError())
    mocker.patch.object(samples, "db", status_db.as_type)

    # GIVEN a request body with a sample internal id and a lims status
    request_body = {
        "samples": [
            {"internal_id": "sample_1", "lims_status": "top-up"},
        ]
    }

    # WHEN calling the endpoint to update the lims status of the sample
    response = client.patch(
        path="/api/v1/samples",
        json=request_body,
    )

    # THEN the response should indicate that the sample was not found
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # THEN the database was not updated
    status_db.as_mock.commit_to_store.assert_not_called()


def test_update_sample_invalid_request_structure(client: FlaskClient, mocker: MockerFixture):
    # GIVEN a store that raises an error when trying to get a sample
    status_db: TypedMock[Store] = create_typed_mock(Store)
    mocker.patch.object(samples, "db", status_db.as_type)

    # GIVEN a request body with an invalid structure
    request_body = {
        "not_samples_keys": [
            {},
        ]
    }

    # WHEN calling the endpoint to update the lims status of the sample
    response = client.patch(
        path="/api/v1/samples",
        json=request_body,
    )

    # THEN the response should indicate that the sample was not found
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # THEN the database was not updated
    status_db.as_mock.commit_to_store.assert_not_called()


def test_get_unhandled_samples(client: FlaskClient, mocker: MockerFixture):
    # GIVEN a store with unhandled samples in top-up
    status_db: TypedMock[Store] = create_typed_mock(Store)
    date_time = datetime(2024, 12, 24, 11, 59)
    sample_1 = create_autospec(
        Sample,
        customer=create_autospec(Customer, interal_id="external_customer"),
        delivered_at=None,
        from_sample=None,
        internal_id="sample_1",
        is_cancelled=False,
        last_sequenced_at=date_time,
        lims_status=LimsStatus.TOP_UP,
        original_workflow=Workflow.RAREDISEASE,
        ticket_id_from_original_order=123456,
    )
    status_db.as_type.get_paginated_unhandled_samples = Mock(return_value=([sample_1], 1))
    mocker.patch.object(samples, "db", status_db.as_type)

    # GIVEN a request to get unhandled samples that are in top-up

    # WHEN calling the endpoint to get unhandled samples
    response = client.get(
        path="/api/v1/unhandled_samples?lims_status=top-up&page=1&page_size=10",
    )

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN samples should be returned
    assert response.json == {
        "samples": [
            {
                "internal_id": "sample_1",
                "last_sequenced_at": "Tue, 24 Dec 2024 11:59:00 GMT",
                "lims_status": "top-up",
                "ticket": 123456,
                "workflow": "raredisease",
            }
        ],
        "total": 1,
    }

    # THEN function has been called with the correct arguments
    status_db.as_mock.get_paginated_unhandled_samples.assert_called_once_with(
        lims_status=LimsStatus.TOP_UP, page=1, page_size=10
    )
