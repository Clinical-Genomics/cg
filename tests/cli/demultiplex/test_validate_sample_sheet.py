from pathlib import Path

from click.testing import CliRunner, Result

from cg.apps.demultiplex.sample_sheet.read_sample_sheet import (
    get_sample_sheet_from_file,
)
from cg.cli.demultiplex.sample_sheet import validate_sample_sheet
from cg.constants import EXIT_SUCCESS, FileExtensions


def test_validate_non_existing_sample_sheet(cli_runner: CliRunner):
    """Test validate sample sheet when sample sheet does not exist."""

    # GIVEN a cli runner
    # GIVEN a sample sheet file that does not exist
    sample_sheet: Path = Path("a_sample_sheet_that_does_not_exist.csv")
    assert sample_sheet.exists() is False

    # WHEN validating the sample sheet
    result = cli_runner.invoke(
        validate_sample_sheet,
        [str(sample_sheet)],
    )

    # THEN assert that it exits with a non-zero exit code
    assert result.exit_code != EXIT_SUCCESS
    # THEN assert the correct information was communicated
    assert f"File '{sample_sheet.name}' does not exist" in result.output


def test_validate_sample_sheet_wrong_file_type(
    cli_runner: CliRunner,
    novaseq_6000_run_parameters_path: Path,
    caplog,
):
    """Test validate sample sheet when sample sheet is in wrong format."""
    # GIVEN an existing file in the wrong file format
    sample_sheet: Path = novaseq_6000_run_parameters_path
    assert sample_sheet.exists()
    assert sample_sheet.suffix != FileExtensions.CSV

    # WHEN validating the sample sheet
    result: Result = cli_runner.invoke(
        validate_sample_sheet,
        [str(sample_sheet)],
    )

    # THEN assert it exits with a non-zero exit code
    assert result.exit_code != EXIT_SUCCESS

    # THEN assert the correct information was communicated
    assert "seems to be in wrong format" in caplog.text


def test_validate_correct_bcl2fastq_sample_sheet(
    cli_runner: CliRunner,
    novaseq_bcl2fastq_sample_sheet_path: Path,
):
    """Test validate sample sheet when using a bcl2fastq sample sheet."""

    # GIVEN the path to a bcl2fastq sample sheet that exists
    sample_sheet: Path = novaseq_bcl2fastq_sample_sheet_path
    assert sample_sheet.exists()

    # GIVEN that the sample sheet is correct
    get_sample_sheet_from_file(sample_sheet)

    # WHEN validating the sample sheet
    result: Result = cli_runner.invoke(
        validate_sample_sheet,
        [str(sample_sheet)],
    )

    # THEN assert that it exits successfully
    assert result.exit_code == EXIT_SUCCESS


def test_validate_correct_dragen_sample_sheet(
    cli_runner: CliRunner,
    novaseq_bcl_convert_sample_sheet_path: Path,
):
    """Test validate sample sheet when using a BCLconvert sample sheet."""

    # GIVEN the path to a Bcl2fastq sample sheet that exists
    sample_sheet: Path = novaseq_bcl_convert_sample_sheet_path
    assert sample_sheet.exists()

    # GIVEN that the sample sheet is correct
    get_sample_sheet_from_file(sample_sheet)

    # WHEN validating the sample sheet
    result: Result = cli_runner.invoke(
        validate_sample_sheet,
        [str(sample_sheet)],
    )

    # THEN assert that it exits successfully
    assert result.exit_code == EXIT_SUCCESS
