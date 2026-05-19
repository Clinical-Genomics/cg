from unittest.mock import create_autospec

from click.testing import CliRunner
from mock import ANY
from pytest_mock import MockerFixture

from cg.apps.tb.api import TrailblazerAPI
from cg.cli.deliver.base import deliver_dev_case_command
from cg.constants.process import EXIT_PARSE_ERROR
from cg.models.cg_config import CGConfig
from cg.services.deliver_service import DeliverService
from cg.store.store import Store


def test_deliver_dev_case_command_success(mocker: MockerFixture):
    # GIVEN a CG config and a case ID
    cli_runner = CliRunner()
    cg_config = create_autospec(
        CGConfig, status_db=create_autospec(Store), trailblazer_api=create_autospec(TrailblazerAPI)
    )

    deliver_case_command = mocker.spy(DeliverService, "deliver_case")

    # WHEN delivering a single case
    cli_runner.invoke(deliver_dev_case_command, ["--signature", "CG", "case_id"], obj=cg_config)

    # THEN the delivery service is called with the expected arguments
    deliver_case_command.assert_called_once_with(ANY, case_id="case_id", signature="CG")


def test_deliver_dev_case_command_no_case_id():
    # GIVEN a CG config
    cli_runner = CliRunner()
    cg_config = create_autospec(
        CGConfig, status_db=create_autospec(Store), trailblazer_api=create_autospec(TrailblazerAPI)
    )

    # WHEN calling the deliver case command without a case id
    result = cli_runner.invoke(deliver_dev_case_command, ["--signature", "CG"], obj=cg_config)

    # THEN the command failed
    assert result.exit_code == EXIT_PARSE_ERROR


def test_deliver_dev_case_command_no_signature():
    # GIVEN a CG config
    cli_runner = CliRunner()
    cg_config = create_autospec(
        CGConfig, status_db=create_autospec(Store), trailblazer_api=create_autospec(TrailblazerAPI)
    )

    # WHEN calling the deliver case command without a signature
    result = cli_runner.invoke(deliver_dev_case_command, ["case_id"], obj=cg_config)

    # THEN the command failed
    assert result.exit_code == EXIT_PARSE_ERROR
