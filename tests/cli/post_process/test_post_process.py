from unittest.mock import create_autospec

from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.post_process import post_process
from cg.cli.post_process.post_process import post_process_all_runs
from cg.cli.post_process.utils import UnprocessedRunInfo
from cg.models.cg_config import CGConfig
from cg.services.run_devices.abstract_classes import PostProcessingService
from tests.typed_mock import TypedMock, create_typed_mock


def test_post_process_all_pacbio_success(mocker: MockerFixture):
    # GIVEN a cg_config
    cg_config: CGConfig = create_autospec(CGConfig)

    # GIVEN a post_processing_service
    post_processing_service: TypedMock[PostProcessingService] = create_typed_mock(
        PostProcessingService
    )

    # GIVEN one run ready to be post processed
    unprocessed_run_info = create_autospec(
        UnprocessedRunInfo,
        instrument="pacbio",
        post_processing_service=post_processing_service.as_type,
    )
    unprocessed_run_info.name = "run_name"

    mocker.patch.object(
        post_process,
        "get_unprocessed_runs_info",
        return_value=[unprocessed_run_info],
    )

    # WHEN calling post_process_all_runs
    cli_runner = CliRunner()
    result = cli_runner.invoke(
        post_process_all_runs, args=["--instrument", "pacbio"], obj=cg_config
    )

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the post processing service should have been called
    post_processing_service.as_mock.post_process.assert_called_once_with(
        run_full_name="run_name", dry_run=False
    )
