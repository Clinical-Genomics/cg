from unittest.mock import create_autospec

from click.testing import CliRunner

from cg.cli.post_process.post_process import post_process_all_runs
from cg.models.cg_config import CGConfig


def test_post_process_all_pacbio_success():
    # GIVEN a cg_config
    cg_config: CGConfig = create_autospec(CGConfig)

    # WHEN calling post_process_all_runs
    cli_runner = CliRunner()
    cli_runner.invoke()
    post_process_all_runs(instrument="pacbio", dry_run=False)

    # THEN the command exits successfully
    # THEN the post processing service should have been called
