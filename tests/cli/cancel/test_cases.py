from unittest.mock import Mock, create_autospec

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.cancel.cases import cases
from cg.cli.cancel.cases import os as os_from_cli
from cg.exc import CgError
from cg.models.cg_config import CGConfig
from cg.services import cancellation_service
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.mark.freeze_time("1908-12-10 13:37")
def test_cases_cancellation_success(mocker: MockerFixture):
    # GIVEN a cg_config with a status_db
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config: CGConfig = create_autospec(CGConfig, status_db=status_db.as_type)

    # GIVEN a mocked cancelation service
    cancel_cases: Mock = mocker.patch.object(cancellation_service, "cases")

    # GIVEN case ids and a comment with a user
    mocker.patch.dict(os_from_cli.environ, {"SUDO_USER": "Ernes.Rutherford"})
    case_ids: list[str] = ["case_1", "case_2"]
    comment = "Customer withdrew the order"

    # WHEN canceling the cases
    result = CliRunner().invoke(cases, args=[*case_ids, "--comment", comment], obj=cg_config)

    # THEN the command exits successfully
    assert result.exit_code == 0, result.output

    # THEN the cancelation service was correctly called
    cancel_cases.assert_called_once_with(
        case_ids=set(case_ids),
        comment=comment,
        user="Ernes.Rutherford",
        status_db=status_db.as_type,
    )

    # THEN the changes were committed
    status_db.as_mock.commit_to_store.assert_called_once()


def test_cases_cancellation_service_error(mocker: MockerFixture):
    # GIVEN a cg_config with a status_db
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config: CGConfig = create_autospec(CGConfig, status_db=status_db.as_type)

    # GIVEN a cancelation service that raises a CgError
    mocker.patch.object(cancellation_service, "cases", side_effect=CgError("Cancellation failed"))

    # GIVEN case ids and a comment
    case_ids: list[str] = ["case_1", "case_2"]
    comment = "Customer withdrew the order"

    # WHEN canceling the cases
    result = CliRunner().invoke(cases, args=[*case_ids, "--comment", comment], obj=cg_config)

    # THEN the command aborts through the expected error path
    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)

    # THEN nothing was committed
    status_db.as_mock.commit_to_store.assert_not_called()

    # THEN the changes were rolled back
    status_db.as_mock.rollback.assert_called_once()


def test_cases_cancellation_unexpected_error(mocker: MockerFixture):
    # GIVEN a cg_config with a status_db
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config: CGConfig = create_autospec(CGConfig, status_db=status_db.as_type)

    # GIVEN a cancelation service that raises an unexpected error
    mocker.patch.object(cancellation_service, "cases", side_effect=ValueError("Unexpected"))

    # GIVEN case ids and a comment
    case_ids: list[str] = ["case_1", "case_2"]
    comment = "Customer withdrew the order"

    # WHEN canceling the cases
    result = CliRunner().invoke(cases, args=[*case_ids, "--comment", comment], obj=cg_config)

    # THEN the unexpected error is re-raised
    assert result.exit_code == 1
    assert isinstance(result.exception, ValueError)

    # THEN nothing was committed
    status_db.as_mock.commit_to_store.assert_not_called()

    # THEN the changes were rolled back
    status_db.as_mock.rollback.assert_called_once()
