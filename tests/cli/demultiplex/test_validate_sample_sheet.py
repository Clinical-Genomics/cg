from pathlib import Path

import pytest
from click.testing import CliRunner, Result

from cg.cli.demultiplex.sample_sheet import validate_sample_sheet
from cg.constants import EXIT_SUCCESS, FileExtensions
from cg.models.cg_config import CGConfig


def test_validate_non_existing_sample_sheet(
    cli_runner: CliRunner,
    sample_sheet_context: CGConfig,
):
    """Test validate sample sheet when sample sheet does not exist."""

    # GIVEN a cli runner
    # GIVEN a sample sheet file that does not exist
    sample_sheet: Path = Path("a_sample_sheet_that_does_not_exist.csv")
    assert sample_sheet.exists() is False

    # WHEN validating the sample sheet
    result = cli_runner.invoke(
        validate_sample_sheet,
        [str(sample_sheet)],
        obj=sample_sheet_context,
    )

    # THEN assert that it exits with a non-zero exit code
    assert result.exit_code != EXIT_SUCCESS
    # THEN assert the correct information was communicated
    assert f"File '{sample_sheet.name}' does not exist" in result.output


def test_validate_sample_sheet_wrong_file_type(
    cli_runner: CliRunner,
    novaseq_6000_run_parameters_pre_1_5_kits_path: Path,
    sample_sheet_context: CGConfig,
    caplog,
):
    """Test validate sample sheet when sample sheet is in wrong format."""
    # GIVEN an existing file in the wrong file format
    sample_sheet: Path = novaseq_6000_run_parameters_pre_1_5_kits_path
    assert sample_sheet.exists()
    assert sample_sheet.suffix != FileExtensions.CSV

    # WHEN validating the sample sheet
    result: Result = cli_runner.invoke(
        validate_sample_sheet,
        [str(sample_sheet)],
        obj=sample_sheet_context,
    )

    # THEN assert it exits with a non-zero exit code
    assert result.exit_code != EXIT_SUCCESS

    # THEN assert the correct information was communicated
    assert "seems to be in wrong format" in caplog.text


@pytest.mark.parametrize(
    "sample_sheet_path",
    [
        "hiseq_x_single_index_sample_sheet_path",
        "hiseq_x_dual_index_sample_sheet_path",
        "hiseq_2500_dual_index_sample_sheet_path",
        "hiseq_2500_custom_index_sample_sheet_path",
        "novaseq_6000_pre_1_5_kits_correct_sample_sheet_path",
        "novaseq_6000_post_1_5_kits_correct_sample_sheet_path",
        "novaseq_x_correct_sample_sheet",
    ],
)
def test_validate_correct_bcl_convert_sample_sheet(
    cli_runner: CliRunner,
    sample_sheet_path: str,
    sample_sheet_context: CGConfig,
    request: pytest.FixtureRequest,
):
    """Test validate sample sheet when using a BCLconvert sample sheet."""

    # GIVEN the path to a correct BCLConvert sample sheet that exists
    sample_sheet: Path = request.getfixturevalue(sample_sheet_path)
    assert sample_sheet.exists()

    # WHEN validating the sample sheet
    result: Result = cli_runner.invoke(
        validate_sample_sheet, [str(sample_sheet)], obj=sample_sheet_context
    )

    # THEN assert that it exits successfully
    assert result.exit_code == EXIT_SUCCESS
