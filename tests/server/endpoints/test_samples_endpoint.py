from datetime import datetime
from http import HTTPStatus
from unittest.mock import Mock, call, create_autospec

from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.constants.lims import LimsStatus
from cg.exc import SampleNotFoundError
from cg.server.dto.samples.requests import SortDirection, UnhandledSamplesSortBy
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
        delivering_case_internal_id="case_1",
        workflow_of_case_that_delivers=Workflow.RAREDISEASE,
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
                "case_id": "case_1",
                "sample_id": "sample_1",
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
        lims_status=LimsStatus.TOP_UP,
        search=None,
        page=1,
        page_size=10,
        sort_by=None,
        sort_order=None,
    )


def test_get_unhandled_samples_invalid_input(client: FlaskClient):
    # GIVEN an unparsable page_size
    # WHEN querying the unhandles samples endpoint
    response = client.get(
        path="/api/v1/unhandled_samples?lims_status=top-up&page=1&page_size=sjutton",
    )

    # THEN we should get a bad request response
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_unhandled_samples_sample_search(client: FlaskClient, mocker: MockerFixture):
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
        delivering_case_internal_id="case_1",
        workflow_of_case_that_delivers=Workflow.RAREDISEASE,
        ticket_id_from_original_order=123456,
    )
    status_db.as_type.get_paginated_unhandled_samples = Mock(return_value=([sample_1], 1))
    mocker.patch.object(samples, "db", status_db.as_type)

    # GIVEN a request to get unhandled samples that are in top-up

    # WHEN calling the endpoint to get unhandled samples
    response = client.get(
        path="/api/v1/unhandled_samples?lims_status=top-up&page=1&page_size=10&search=sample_1",
    )

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN samples should be returned
    assert response.json == {
        "samples": [
            {
                "case_id": "case_1",
                "sample_id": "sample_1",
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
        lims_status=LimsStatus.TOP_UP,
        search="sample_1",
        page=1,
        page_size=10,
        sort_by=None,
        sort_order=None,
    )


def test_get_unhandled_samples_sort_ticket_ascending(client: FlaskClient, mocker: MockerFixture):
    # GIVEN a store with unhandled samples in top-up
    status_db: TypedMock[Store] = create_typed_mock(Store)
    date_time = datetime(2024, 12, 24, 11, 59)
    sample_larger_ticket_number = create_autospec(
        Sample,
        customer=create_autospec(Customer, interal_id="external_customer"),
        delivered_at=None,
        from_sample=None,
        internal_id="sample_larger_ticket_number",
        is_cancelled=False,
        last_sequenced_at=date_time,
        lims_status=LimsStatus.TOP_UP,
        delivering_case_internal_id="case_1",
        workflow_of_case_that_delivers=Workflow.RAREDISEASE,
        ticket_id_from_original_order=2,
    )
    sample_smaller_ticket_number = create_autospec(
        Sample,
        customer=create_autospec(Customer, interal_id="external_customer"),
        delivered_at=None,
        from_sample=None,
        internal_id="sample_smaller_ticket_number",
        is_cancelled=False,
        last_sequenced_at=date_time,
        lims_status=LimsStatus.TOP_UP,
        delivering_case_internal_id="case_2",
        workflow_of_case_that_delivers=Workflow.RAREDISEASE,
        ticket_id_from_original_order=1,
    )
    sample_case_unknown = create_autospec(
        Sample,
        customer=create_autospec(Customer, interal_id="external_customer"),
        delivered_at=None,
        from_sample=None,
        internal_id="sample_case_unknown",
        is_cancelled=False,
        last_sequenced_at=date_time,
        lims_status=LimsStatus.TOP_UP,
        delivering_case_internal_id=None,
        workflow_of_case_that_delivers=None,
        ticket_id_from_original_order=None,
    )
    status_db.as_type.get_paginated_unhandled_samples = Mock(
        return_value=(
            [sample_case_unknown, sample_smaller_ticket_number, sample_larger_ticket_number],
            3,
        )
    )
    mocker.patch.object(samples, "db", status_db.as_type)

    # WHEN querying the unhandles samples endpoint with sorting on ticket
    response = client.get(
        path="/api/v1/unhandled_samples?lims_status=top-up&page=1&page_size=10&sort_by=ticket&sort_order=asc",
    )

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN samples should be returned
    assert response.json == {
        "samples": [
            {
                "case_id": "unknown",
                "sample_id": "sample_case_unknown",
                "last_sequenced_at": "Tue, 24 Dec 2024 11:59:00 GMT",
                "lims_status": "top-up",
                "ticket": "unknown",
                "workflow": "unknown",
            },
            {
                "case_id": "case_2",
                "sample_id": "sample_smaller_ticket_number",
                "last_sequenced_at": "Tue, 24 Dec 2024 11:59:00 GMT",
                "lims_status": "top-up",
                "ticket": 1,
                "workflow": "raredisease",
            },
            {
                "case_id": "case_1",
                "sample_id": "sample_larger_ticket_number",
                "last_sequenced_at": "Tue, 24 Dec 2024 11:59:00 GMT",
                "lims_status": "top-up",
                "ticket": 2,
                "workflow": "raredisease",
            },
        ],
        "total": 3,
    }

    # THEN function has been called with the correct arguments
    status_db.as_mock.get_paginated_unhandled_samples.assert_called_once_with(
        lims_status=LimsStatus.TOP_UP,
        page=1,
        page_size=10,
        search=None,
        sort_by=UnhandledSamplesSortBy.TICKET,
        sort_order=SortDirection.ASCENDING,
    )


def test_get_unhandled_samples_sort_ticket_descending(client: FlaskClient, mocker: MockerFixture):
    # GIVEN a store with unhandled samples in top-up
    status_db: TypedMock[Store] = create_typed_mock(Store)
    date_time = datetime(2024, 12, 24, 11, 59)
    sample_larger_ticket_number = create_autospec(
        Sample,
        customer=create_autospec(Customer, interal_id="external_customer"),
        delivered_at=None,
        from_sample=None,
        internal_id="sample_larger_ticket_number",
        is_cancelled=False,
        last_sequenced_at=date_time,
        lims_status=LimsStatus.TOP_UP,
        delivering_case_internal_id="case_1",
        workflow_of_case_that_delivers=Workflow.RAREDISEASE,
        ticket_id_from_original_order=2,
    )
    sample_smaller_ticket_number = create_autospec(
        Sample,
        customer=create_autospec(Customer, interal_id="external_customer"),
        delivered_at=None,
        from_sample=None,
        internal_id="sample_smaller_ticket_number",
        is_cancelled=False,
        last_sequenced_at=date_time,
        lims_status=LimsStatus.TOP_UP,
        delivering_case_internal_id="case_2",
        workflow_of_case_that_delivers=Workflow.RAREDISEASE,
        ticket_id_from_original_order=1,
    )
    sample_case_unkown = create_autospec(
        Sample,
        customer=create_autospec(Customer, interal_id="external_customer"),
        delivered_at=None,
        from_sample=None,
        internal_id="sample_case_unkown",
        is_cancelled=False,
        last_sequenced_at=date_time,
        lims_status=LimsStatus.TOP_UP,
        delivering_case_internal_id=None,
        workflow_of_case_that_delivers=None,
        ticket_id_from_original_order=None,
    )
    status_db.as_type.get_paginated_unhandled_samples = Mock(
        return_value=(
            [sample_larger_ticket_number, sample_smaller_ticket_number, sample_case_unkown],
            3,
        )
    )
    mocker.patch.object(samples, "db", status_db.as_type)

    # WHEN querying the unhandled samples endpoint with descending sort on ticket
    response = client.get(
        path="/api/v1/unhandled_samples?lims_status=top-up&page=1&page_size=10&sort_by=ticket&sort_order=desc",
    )

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN samples should be returned
    assert response.json == {
        "samples": [
            {
                "case_id": "case_1",
                "sample_id": "sample_larger_ticket_number",
                "last_sequenced_at": "Tue, 24 Dec 2024 11:59:00 GMT",
                "lims_status": "top-up",
                "ticket": 2,
                "workflow": "raredisease",
            },
            {
                "case_id": "case_2",
                "sample_id": "sample_smaller_ticket_number",
                "last_sequenced_at": "Tue, 24 Dec 2024 11:59:00 GMT",
                "lims_status": "top-up",
                "ticket": 1,
                "workflow": "raredisease",
            },
            {
                "case_id": "unknown",
                "sample_id": "sample_case_unkown",
                "last_sequenced_at": "Tue, 24 Dec 2024 11:59:00 GMT",
                "lims_status": "top-up",
                "ticket": "unknown",
                "workflow": "unknown",
            },
        ],
        "total": 3,
    }

    # THEN function has been called with the correct arguments
    status_db.as_mock.get_paginated_unhandled_samples.assert_called_once_with(
        lims_status=LimsStatus.TOP_UP,
        page=1,
        page_size=10,
        search=None,
        sort_by=UnhandledSamplesSortBy.TICKET,
        sort_order=SortDirection.DESCENDING,
    )


def test_get_unhandled_samples_filter_on_workflow(client: FlaskClient, mocker: MockerFixture):
    # GIVEN a store with unhandled samples in top-up
    status_db: TypedMock[Store] = create_typed_mock(Store)
    date_time = datetime(2024, 12, 24, 11, 59)
    sample_1_raredisease = create_autospec(
        Sample,
        customer=create_autospec(Customer, interal_id="external_customer"),
        delivered_at=None,
        from_sample=None,
        internal_id="sample_1_raredisease",
        is_cancelled=False,
        last_sequenced_at=date_time,
        lims_status=LimsStatus.TOP_UP,
        delivering_case_internal_id="case_1",
        workflow_of_case_that_delivers=Workflow.RAREDISEASE,
        ticket_id_from_original_order=2,
    )
    sample_2_raredisease = create_autospec(
        Sample,
        customer=create_autospec(Customer, interal_id="external_customer"),
        delivered_at=None,
        from_sample=None,
        internal_id="sample_2_raredisease",
        is_cancelled=False,
        last_sequenced_at=date_time,
        lims_status=LimsStatus.TOP_UP,
        delivering_case_internal_id="case_2",
        workflow_of_case_that_delivers=Workflow.RAREDISEASE,
        ticket_id_from_original_order=1,
    )
    sample_case_unkown = create_autospec(
        Sample,
        customer=create_autospec(Customer, interal_id="external_customer"),
        delivered_at=None,
        from_sample=None,
        internal_id="sample_case_unkown",
        is_cancelled=False,
        last_sequenced_at=date_time,
        lims_status=LimsStatus.TOP_UP,
        delivering_case_internal_id=None,
        workflow_of_case_that_delivers=None,
        ticket_id_from_original_order=None,
    )
    status_db.as_type.get_paginated_unhandled_samples = Mock(
        return_value=(
            [sample_1_raredisease, sample_2_raredisease, sample_case_unkown],
            3,
        )
    )
    mocker.patch.object(samples, "db", status_db.as_type)

    # WHEN querying the unhandled samples endpoint with workflow Raredisease
    response = client.get(
        path=f"/api/v1/unhandled_samples?lims_status=top-up&page=1&page_size=10&workflow={Workflow.RAREDISEASE}",
    )

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN only samples with workflow raredisease should be in the response
    assert response.json == {
        "samples": [
            {
                "case_id": "case_1",
                "sample_id": "sample_1_raredisease",
                "last_sequenced_at": "Tue, 24 Dec 2024 11:59:00 GMT",
                "lims_status": "top-up",
                "ticket": 2,
                "workflow": "raredisease",
            },
            {
                "case_id": "case_2",
                "sample_id": "sample_2_raredisease",
                "last_sequenced_at": "Tue, 24 Dec 2024 11:59:00 GMT",
                "lims_status": "top-up",
                "ticket": 1,
                "workflow": "raredisease",
            },
        ],
        "total": 2,
    }

    # THEN function has been called with the correct arguments
    status_db.as_mock.get_paginated_unhandled_samples.assert_called_once_with(
        lims_status=LimsStatus.TOP_UP,
        page=1,
        page_size=10,
        search=None,
        sort_by=None,
        sort_order=None,
        workflow=Workflow.RAREDISEASE,
    )


def test_get_unhandled_samples_unknown_param(client: FlaskClient, mocker: MockerFixture):
    # GIVEN an unknown param in the request

    # WHEN querying the unhandled samples endpoint with descending sort on ticket
    response = client.get(
        path="/api/v1/unhandled_samples?lims_status=top-up&page=1&page_size=10&search=whatIsThis?",
    )

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK
