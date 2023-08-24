"""Tests cli methods to create the case config for rnafusion."""

import logging
from pathlib import Path

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import config_case
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from tests.models.rnafusion.conftest import fixture_rnafusion_strandedness_not_acceptable

LOG = logging.getLogger(__name__)


def test_without_options(cli_runner: CliRunner, rnafusion_context: CGConfig):
    """Test command without case_id."""
    # GIVEN NO case

    # WHEN running
    result = cli_runner.invoke(config_case, obj=rnafusion_context)

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command log should inform about missing arguments
    assert "Missing argument" in result.output


def test_with_missing_case(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
):
    """Test command with invalid case to start with."""
    caplog.set_level(logging.ERROR)

    # GIVEN a case not in the StatusDB database
    assert not rnafusion_context.status_db.get_case_by_internal_id(
        internal_id=case_id_does_not_exist
    )
    # WHEN running
    result = cli_runner.invoke(config_case, [case_id_does_not_exist], obj=rnafusion_context)

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN the error log should indicate that the case is invalid
    assert "could not be found in Status DB!" in caplog.text


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
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
    rnafusion_sample_sheet_path: Path,
    rnafusion_params_file_path: Path,
):
    """Test that command generates default config files."""
    caplog.set_level(logging.INFO)

    # GIVEN a valid case

    # WHEN running config case
    result = cli_runner.invoke(config_case, [rnafusion_case_id], obj=rnafusion_context)

    # THEN command should exit succesfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN sample sheet file should be generated
    assert "Getting sample sheet information" in caplog.text
    assert "Writing sample sheet" in caplog.text

    # THEN parameters file should be generated
    assert "Getting parameters information" in caplog.text
    assert "Writing parameters file" in caplog.text
    assert rnafusion_sample_sheet_path.is_file()
    assert rnafusion_params_file_path.is_file()


def test_dry_run(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
):
    """Test dry-run."""
    caplog.set_level(logging.INFO)

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
