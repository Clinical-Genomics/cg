"""Tests cli methods to create the case config for Taxprofiler."""

import logging
from pathlib import Path

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.taxprofiler.base import config_case
from cg.constants import EXIT_SUCCESS
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.models.cg_config import CGConfig
from cg.models.taxprofiler.taxprofiler import (
    TaxprofilerParameters,
    TaxprofilerSampleSheetEntry,
)


def test_config_case_default_parameters(
    cli_runner: CliRunner,
    taxprofiler_context: CGConfig,
    taxprofiler_case_id: str,
    taxprofiler_sample_sheet_path: Path,
    taxprofiler_params_file_path: Path,
    taxprofiler_sample_sheet_content: str,
    taxprofiler_parameters_default: TaxprofilerParameters,
    caplog: LogCaptureFixture,
):
    """Test that command generates default config files."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a valid case

    # WHEN running config case
    result = cli_runner.invoke(config_case, [taxprofiler_case_id], obj=taxprofiler_context)

    # THEN command should exit successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN logs should be as expected
    expected_logs: list[str] = [
        "Getting sample sheet information",
        "Writing sample sheet",
        "Getting parameters information",
        "Writing parameters file",
    ]
    for expected_log in expected_logs:
        assert expected_log in expected_logs

    # THEN files should be generated
    assert taxprofiler_sample_sheet_path.is_file()
    assert taxprofiler_params_file_path.is_file()

    # THEN the sample sheet content should match the expected values
    sample_sheet_content: list[list[str]] = ReadFile.get_content_from_file(
        file_format=FileFormat.TXT, file_path=taxprofiler_sample_sheet_path, read_to_string=True
    )
    assert ",".join(TaxprofilerSampleSheetEntry.headers()) in sample_sheet_content
    assert taxprofiler_sample_sheet_content in sample_sheet_content

    # THEN the params file should contain all parameters
    params_content: list[list[str]] = ReadFile.get_content_from_file(
        file_format=FileFormat.TXT, file_path=taxprofiler_params_file_path, read_to_string=True
    )
    for parameter in vars(taxprofiler_parameters_default).keys():
        assert parameter in params_content


def test_config_case_dry_run(
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
