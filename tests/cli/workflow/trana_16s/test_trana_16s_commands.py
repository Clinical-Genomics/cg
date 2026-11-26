from unittest.mock import create_autospec

from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.apps.tb.api import TrailblazerAPI
from cg.cli.workflow.trana_16s.trana_16s_commands import analysis_qc_service, perform_qc_check
from cg.models.cg_config import CGConfig, TranaConfig
from cg.store.store import Store


def test_perform_qc_check(mocker: MockerFixture):
    # GIVEN a CGConfig
    cg_config: CGConfig = create_autospec(
        CGConfig,
        trana_16s=create_autospec(TranaConfig, root="root_dir"),
        status_db=create_autospec(Store),
        trailblazer_api=create_autospec(TrailblazerAPI),
    )
    cli_runner = CliRunner()

    perform_qc_mock = mocker.patch.object(analysis_qc_service, "perform_qc")

    # WHEN calling perform_qc_check
    cli_runner.invoke(perform_qc_check, obj=cg_config)

    # THEN perform_qc was called with the correct parameters
    perform_qc_mock.assert_called_once_with(
        root_directory="root_dir",
        status_db=cg_config.status_db,
        trailblazer_api=cg_config.trailblazer_api,
        analysis_id=2,
    )
