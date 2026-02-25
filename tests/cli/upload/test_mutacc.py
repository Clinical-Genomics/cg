from unittest.mock import create_autospec

from click.testing import CliRunner

from cg.cli.upload.mutacc import process_solved
from cg.models.cg_config import CGConfig, IlluminaConfig, RunInstruments


def test_process_solved_success():
    # GIVEN a cg config
    cg_config = create_autospec(
        CGConfig,
        delivery_path="delivery/path",
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
    )

    # GIVEN a cli_runner
    cli_runner = CliRunner()
    cli_runner.invoke(process_solved, ["--scout-instance", "hg19"], obj=cg_config)

    #
