"""Tests cli methods to create the case config for Rnafusion."""

import logging
from pathlib import Path
from typing import List

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import config_case
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.models.rnafusion.rnafusion import RnafusionParameters, RnafusionSample

LOG = logging.getLogger(__name__)


def test_without_samples(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    no_sample_case_id: str,
):
    """Test command with case_id and no samples."""
    caplog.set_level(logging.ERROR)
    # GIVEN a case

    # WHEN running config case
    result = cli_runner.invoke(config_case, [no_sample_case_id], obj=rnafusion_context)

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no sample is found
    assert no_sample_case_id in caplog.text
    assert "has no samples" in caplog.text


def test_wrong_strandedness(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
    rnafusion_strandedness_not_acceptable: str,
):
    """Test command with --strandedness option."""
    caplog.set_level(logging.ERROR)

    # GIVEN a VALID case_id and non-accepted strandedness option

    # WHEN running with strandedness option specified
    result = cli_runner.invoke(
        config_case,
        [rnafusion_case_id, "--strandedness", rnafusion_strandedness_not_acceptable],
        obj=rnafusion_context,
    )

    # THEN command should fail
    assert result.exit_code != EXIT_SUCCESS
    assert "Could not create config files for" in caplog.text
    assert "validation error" in caplog.text


def test_defaults(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    rnafusion_case_id: str,
    rnafusion_sample_sheet_path: Path,
    rnafusion_params_file_path: Path,
    rnafusion_sample_sheet_content: str,
    caplog: LogCaptureFixture,
):
    """Test that command generates default config files."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a valid case

    # WHEN running config case
    result = cli_runner.invoke(config_case, [rnafusion_case_id], obj=rnafusion_context)

    # THEN command should exit succesfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN logs should be as expected
    expected_logs: List[str] = [
        "Getting sample sheet information",
        "Writing sample sheet",
        "Getting parameters information",
        "Writing parameters file",
    ]
    for expected_log in expected_logs:
        assert expected_log in expected_logs

    # THEN files should be generated
    assert rnafusion_sample_sheet_path.is_file()
    assert rnafusion_params_file_path.is_file()

    # THEN the sample sheet content should match the expected values
    with rnafusion_sample_sheet_path.open("r") as file:
        content = file.read()
        assert ",".join(RnafusionSample.headers()) in content
        assert rnafusion_sample_sheet_content in content

    # THEN the params file should contain all parameters
    with rnafusion_params_file_path.open("r") as file:
        content = file.read()
        for parameter in RnafusionParameters.__annotations__.keys():
            assert parameter in content


def test_dry_run(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
):
    """Test dry-run."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a valid case

    # WHEN performing a dry-run
    result = cli_runner.invoke(config_case, [rnafusion_case_id, "-d"], obj=rnafusion_context)

    # THEN command should should exit succesfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN sample sheet and parameters information should be collected
    assert "Getting sample sheet information" in caplog.text
    assert "Getting parameters information" in caplog.text

    # THEN sample sheet and parameters information files should not be written
    assert "Dry run: Config files will not be written" in caplog.text
    assert "Writing sample sheet" not in caplog.text
    assert "Writing parameters file" not in caplog.text


def test_reference(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
    rnafusion_params_file_path: Path,
):
    """Test command with given reference directory."""
    caplog.set_level(logging.INFO)

    # GIVEN a valid case and reference dir
    reference_dir: str = Path("non", "default", "path", "to", "references").as_posix()

    # WHEN running config case
    result = cli_runner.invoke(
        config_case,
        [rnafusion_case_id, "--genomes_base", reference_dir],
        obj=rnafusion_context,
    )

    # THEN command should exit successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN parameters file should be generated
    assert rnafusion_params_file_path.is_file()

    # THEN the given reference directory should be written
    with rnafusion_params_file_path.open("r") as file:
        content = file.read()
        assert reference_dir in content
