"""Tests cli methods to create the case config for Taxprofiler."""

import logging
from pathlib import Path
from typing import List

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.taxprofiler.base import config_case
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.models.taxprofiler.taxprofiler import TaxprofilerParameters, TaxprofilerSample


def test_defaults(
    cli_runner: CliRunner,
    taxprofiler_context: CGConfig,
    taxprofiler_case_id: str,
    taxprofiler_sample_sheet_path: Path,
    taxprofiler_params_file_path: Path,
    taxprofiler_sample_sheet_content: str,
    caplog: LogCaptureFixture,
):
    """Test that command generates default config files."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a valid case

    # WHEN running config case
    result = cli_runner.invoke(config_case, [taxprofiler_case_id], obj=taxprofiler_context)

    # THEN command should exit successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN sample sheet file should be generated
    assert "Getting sample sheet information" in caplog.text
    assert "Writing sample sheet" in caplog.text

    # THEN parameters file should be generated
    assert "Getting parameters information" in caplog.text
    assert "Writing parameters file" in caplog.text
    assert taxprofiler_sample_sheet_path.is_file()
    assert taxprofiler_params_file_path.is_file()

    # THEN the sample sheet content should match the expected values
    with taxprofiler_sample_sheet_path.open("r") as file:
        content = file.read()
        assert ",".join(TaxprofilerSample.headers()) in content
        assert taxprofiler_sample_sheet_content in content

    # THEN the params file should contain all parameters
    with taxprofiler_params_file_path.open("r") as file:
        content = file.read()
        for parameter in TaxprofilerParameters.__annotations__.keys():
            assert parameter in content


def test_dry_run(
    cli_runner: CliRunner,
    taxprofiler_context: CGConfig,
    caplog: LogCaptureFixture,
    taxprofiler_case_id: str,
):
    """Test dry-run."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a valid case

    # WHEN performing a dry-run
    result = cli_runner.invoke(config_case, [taxprofiler_case_id, "-d"], obj=taxprofiler_context)

    # THEN command should should exit succesfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN sample sheet and parameters information should be collected
    assert "Getting sample sheet information" in caplog.text
    assert "Getting parameters information" in caplog.text

    # THEN sample sheet and parameters information files should not be written
    assert "Dry run: Config files will not be written" in caplog.text
    assert "Writing sample sheet" not in caplog.text
    assert "Writing parameters file" not in caplog.text
