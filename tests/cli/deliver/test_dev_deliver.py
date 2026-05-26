from unittest.mock import create_autospec

import pytest
from click.testing import CliRunner
from mock import ANY
from pytest_mock import MockerFixture

from cg.apps.tb.api import TrailblazerAPI
from cg.cli.deliver.base import deliver_dev_all_cases, deliver_dev_case_command, deliver_dev_order
from cg.constants.process import EXIT_FAIL, EXIT_PARSE_ERROR, EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.services.deliver_service import DeliverService
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_deliver_dev_case_command_success(mocker: MockerFixture):
    # GIVEN a store, a CG config and a case ID
    cli_runner = CliRunner()
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config = create_autospec(
        CGConfig, status_db=status_db.as_type, trailblazer_api=create_autospec(TrailblazerAPI)
    )

    deliver_case_command = mocker.spy(DeliverService, "deliver_case")

    # WHEN delivering a single case
    result = cli_runner.invoke(
        deliver_dev_case_command, ["--signature", "CG", "case_id"], obj=cg_config
    )

    # THEN the command should have exited successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the delivery service is called with the expected arguments
    deliver_case_command.assert_called_once_with(ANY, case_id="case_id", signature="CG")

    # THEN the changes were persisted in the database
    status_db.as_mock.commit_to_store.assert_called_once()


def test_deliver_dev_case_command_no_case_id():
    # GIVEN a store and a CG config
    cli_runner = CliRunner()
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config = create_autospec(
        CGConfig, status_db=status_db.as_type, trailblazer_api=create_autospec(TrailblazerAPI)
    )

    # WHEN calling the deliver case command without a case id
    result = cli_runner.invoke(deliver_dev_case_command, ["--signature", "CG"], obj=cg_config)

    # THEN the command failed
    assert result.exit_code == EXIT_PARSE_ERROR

    # THEN the changes were NOT persisted in the database
    status_db.as_mock.commit_to_store.assert_not_called()


def test_deliver_dev_case_command_no_signature():
    # GIVEN a store and a CG config
    cli_runner = CliRunner()
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config = create_autospec(
        CGConfig, status_db=status_db.as_type, trailblazer_api=create_autospec(TrailblazerAPI)
    )

    # WHEN calling the deliver case command without a signature
    result = cli_runner.invoke(deliver_dev_case_command, ["case_id"], obj=cg_config)

    # THEN the command failed
    assert result.exit_code == EXIT_PARSE_ERROR

    # THEN the changes were NOT persistent in the database
    status_db.as_mock.commit_to_store.assert_not_called()


def test_deliver_dev_case_raises_error(mocker: MockerFixture):
    # GIVEN a store and a CG config
    cli_runner = CliRunner()
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config = create_autospec(
        CGConfig, status_db=status_db.as_type, trailblazer_api=create_autospec(TrailblazerAPI)
    )

    # GIVEN that the deliver service raises an error
    mocker.patch.object(DeliverService, "deliver_case", side_effect=Exception)

    # WHEN calling the deliver case command
    result = cli_runner.invoke(
        deliver_dev_case_command, ["--signature", "CG", "case_id"], obj=cg_config
    )

    # THEN the command failed due to service error
    assert result.exit_code == EXIT_FAIL

    # THEN the changes were NOT persistent in the database
    status_db.as_mock.commit_to_store.assert_not_called()


def test_deliver_dev_all_available_command_success(mocker: MockerFixture):
    # GIVEN a store, a CG config and a case ID
    cli_runner = CliRunner()
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config = create_autospec(
        CGConfig, status_db=status_db.as_type, trailblazer_api=create_autospec(TrailblazerAPI)
    )

    deliver_all_command = mocker.spy(DeliverService, "deliver_all_cases")

    # WHEN delivering all available cases
    result = cli_runner.invoke(deliver_dev_all_cases, obj=cg_config)

    # THEN the command should have exited successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the delivery service is called with the expected arguments
    deliver_all_command.assert_called_once_with(ANY)

    # THEN the changes were persistent in the database
    status_db.as_mock.commit_to_store.assert_called_once()


def test_deliver_dev_all_available_service_raises_error(mocker: MockerFixture):
    # GIVEN a store and a CG config
    cli_runner = CliRunner()
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config = create_autospec(
        CGConfig, status_db=status_db.as_type, trailblazer_api=create_autospec(TrailblazerAPI)
    )

    # GIVEN that the deliver service raises an error
    mocker.patch.object(DeliverService, "deliver_all_cases", side_effect=Exception)

    # WHEN calling the deliver all available cases command
    result = cli_runner.invoke(deliver_dev_all_cases, obj=cg_config)

    # THEN the command failed due to service error
    assert result.exit_code == EXIT_FAIL

    # THEN the changes were NOT persistent in the database
    status_db.as_mock.commit_to_store.assert_not_called()


def test_deliver_dev_order(mocker: MockerFixture):
    # GIVEN a store and a CG Config
    cli_runner = CliRunner()
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config = create_autospec(
        CGConfig, status_db=status_db.as_type, trailblazer_api=create_autospec(TrailblazerAPI)
    )

    deliver_order = mocker.spy(DeliverService, "deliver_order")

    # WHEN delivering a single order
    result = cli_runner.invoke(
        deliver_dev_order, ["--ticket-id", "123", "--signature", "CG"], obj=cg_config
    )

    # THEN the command should have exited successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the delivery service is called with the expected arguments
    deliver_order.assert_called_once_with(ANY, signature="CG", ticket_id=123)

    # THEN the changes were persistent in the database
    status_db.as_mock.commit_to_store.assert_called_once()


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["--signature", "CG"],
        ["--ticket-id", "1234567"],
    ],
    ids=[
        "no parameters",
        "missing ticket-id",
        "missing signature",
    ],
)
def test_deliver_dev_order_no_ticket_id(args: list[str]):
    # GIVEN a store and a CG config
    cli_runner = CliRunner()
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config = create_autospec(
        CGConfig, status_db=status_db.as_type, trailblazer_api=create_autospec(TrailblazerAPI)
    )

    # WHEN calling the deliver order command with at least one missing parameter
    result = cli_runner.invoke(deliver_dev_order, args=args, obj=cg_config)

    # THEN the command failed
    assert result.exit_code == EXIT_PARSE_ERROR

    # THEN the changes were NOT persisted in the database
    status_db.as_mock.commit_to_store.assert_not_called()


def test_deliver_dev_order_service_raises_error(mocker: MockerFixture):
    # GIVEN a store and a CG config
    cli_runner = CliRunner()
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config = create_autospec(
        CGConfig, status_db=status_db.as_type, trailblazer_api=create_autospec(TrailblazerAPI)
    )

    # GIVEN that the deliver service raises an error
    mocker.patch.object(DeliverService, "deliver_order", side_effect=Exception)

    # WHEN calling the deliver order command
    result = cli_runner.invoke(
        deliver_dev_order, ["--ticket-id", "743298", "--signature", "CG"], obj=cg_config
    )

    # THEN the command failed due to service error
    assert result.exit_code == EXIT_FAIL

    # THEN the changes were NOT persisted in the database
    status_db.as_mock.commit_to_store.assert_not_called()
