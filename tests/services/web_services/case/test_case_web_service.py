from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.exc import CaseNotFoundError
from cg.services import cancellation_service
from cg.services.web_services.case.service import CaseWebService
from cg.store.models import Case
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.fixture
def store_with_cases() -> TypedMock[Store]:
    """Return a mocked store where entry ids 1 and 2 map to two cases."""
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cases: dict[str, Case] = {
        "1": create_autospec(Case, instance=True, internal_id="amazingdog"),
        "2": create_autospec(Case, instance=True, internal_id="shittycow"),
    }
    status_db.as_mock.get_case_by_entry_id.side_effect = lambda entry_id: cases[entry_id]
    return status_db


def test_cancel_cases_success(mocker: MockerFixture, store_with_cases: TypedMock[Store]):
    # GIVEN a case web service
    case_web_service = CaseWebService(store=store_with_cases.as_type)

    # GIVEN a mocked cancellation service
    cancel_cases: Mock = mocker.patch.object(cancellation_service, "cases")

    # WHEN cancelling cases by their entry ids
    message: str = case_web_service.cancel_cases(
        entry_ids=["1", "2"], user_email="ernes.rutherford@scilifelab.se"
    )

    # THEN the cancellation service is called with the internal ids of the cases
    cancel_cases.assert_called_once_with(
        case_ids={"amazingdog", "shittycow"},
        comment="Cancelled in admin view",
        user="ernes.rutherford@scilifelab.se",
        status_db=store_with_cases.as_type,
    )

    # THEN the changes are committed
    store_with_cases.as_mock.commit_to_store.assert_called_once()
    store_with_cases.as_mock.rollback.assert_not_called()

    # THEN the message names the cancelled cases
    assert message == "Cancelled cases: amazingdog, shittycow"


@pytest.mark.parametrize(
    "error",
    [CaseNotFoundError("Cases not found: amazingdog"), ValueError("Unexpected")],
    ids=["expected_error", "unexpected_error"],
)
def test_cancel_cases_cancellation_fails(
    mocker: MockerFixture, store_with_cases: TypedMock[Store], error: Exception
):
    # GIVEN a case web service
    case_web_service = CaseWebService(store=store_with_cases.as_type)

    # GIVEN a cancellation service that raises an error
    mocker.patch.object(cancellation_service, "cases", side_effect=error)

    # WHEN cancelling cases
    # THEN the original error is re-raised
    with pytest.raises(type(error)) as exc_info:
        case_web_service.cancel_cases(entry_ids=["1"], user_email="ernes.rutherford@scilifelab.se")
    assert exc_info.value is error

    # THEN nothing is committed and the changes are rolled back
    store_with_cases.as_mock.commit_to_store.assert_not_called()
    store_with_cases.as_mock.rollback.assert_called_once()


def test_cancel_cases_commit_fails(mocker: MockerFixture, store_with_cases: TypedMock[Store]):
    # GIVEN a case web service
    case_web_service = CaseWebService(store=store_with_cases.as_type)

    # GIVEN a mocked cancellation service
    mocker.patch.object(cancellation_service, "cases")

    # GIVEN that committing to the store fails
    store_with_cases.as_mock.commit_to_store.side_effect = ValueError("Commit failed")

    # WHEN cancelling cases
    # THEN the error is re-raised
    with pytest.raises(ValueError):
        case_web_service.cancel_cases(entry_ids=["1"], user_email="ernes.rutherford@scilifelab.se")

    # THEN the changes are rolled back
    store_with_cases.as_mock.rollback.assert_called_once()
