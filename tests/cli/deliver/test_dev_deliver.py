from unittest.mock import create_autospec

from click.testing import CliRunner
from mock import ANY
from pytest_mock import MockerFixture

from cg.apps.tb.api import TrailblazerAPI
from cg.cli.deliver.base import deliver_dev_case_command
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
    deliver_case_command.assert_called_once_with(ANY)

    pass


def test_deliver_dev_case_command_no_case_id():
    pass


def test_deliver_dev_case_command_no_signature():
    pass
