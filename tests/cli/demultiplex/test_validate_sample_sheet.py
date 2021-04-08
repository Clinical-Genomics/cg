from pathlib import Path

from cg.cli.demultiplex.sample_sheet import validate_sample_sheet
from cgmodels.demultiplex.sample_sheet import get_sample_sheet_from_file
from click.testing import CliRunner, Result


def test_validate_non_existing_sample_sheet(cli_runner: CliRunner, sample_sheet_context: dict):
    # GIVEN a cli runner
    # GIVEN a sample sheet file that does not exist
    sample_sheet: Path = Path("a_sample_sheet.csv")
    assert sample_sheet.exists() is False

    # WHEN validating the sample sheet
    result = cli_runner.invoke(validate_sample_sheet, [str(sample_sheet)], obj=sample_sheet_context)

    # THEN assert that it exits with a non zero exit code
    assert result.exit_code != 0
    # THEN assert the correct information was communicated
    assert f'Path "{sample_sheet.name}" does not exist' in result.output


def test_validate_sample_sheet_wrong_file_type(
    cli_runner: CliRunner, sample_sheet_context: dict, novaseq_run_parameters: Path, caplog
):
    # GIVEN a existing file in the wrong file format
    sample_sheet = novaseq_run_parameters
    assert sample_sheet.exists()
    assert sample_sheet.suffix != ".csv"

    # WHEN validating the sample sheet
    result: Result = cli_runner.invoke(
        validate_sample_sheet, [str(sample_sheet)], obj=sample_sheet_context
    )

    # THEN assert it exits with a non zero exit code
    assert result.exit_code != 0

    # THEN assert the correct information was communicated
    assert "seems to be in wrong format" in caplog.text


def test_validate_correct_sample_sheet(
    cli_runner: CliRunner, sample_sheet_context: dict, novaseq_sample_sheet_path: Path
):
    # GIVEN the path to a sample sheet that exists
    sample_sheet: Path = novaseq_sample_sheet_path
    assert sample_sheet.exists()
    # GIVEN that the sample sheet is correct
    get_sample_sheet_from_file(infile=sample_sheet, sheet_type="S2")

    # WHEN validating the sample sheet
    result: Result = cli_runner.invoke(
        validate_sample_sheet, [str(sample_sheet)], obj=sample_sheet_context
    )

    # THEN assert that it exits without any problems
    assert result.exit_code == 0
