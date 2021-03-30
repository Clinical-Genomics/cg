from pathlib import Path

from cg.apps.demultiplex.flowcell import Flowcell
from cg.cli.demultiplex.base import create_sample_sheet
from click import testing


def test_create_sample_sheet_no_run_parameters(
    cli_runner: testing.CliRunner, demultiplex_fixtures: Path, sample_sheet_context: dict, caplog
):
    # GIVEN a folder with a non existing sample sheet
    flowcell_object: Flowcell = Flowcell(demultiplex_fixtures)
    assert flowcell_object.run_parameters_path.exists() is False

    # WHEN running the create sample sheet command
    result: testing.Result = cli_runner.invoke(
        create_sample_sheet, [str(demultiplex_fixtures)], obj=sample_sheet_context
    )

    # THEN assert it exits with a non zero exit code
    assert result.exit_code != 0
    # THEN assert the correct information is communicated
    assert "Run parameters is missing, can not create sample sheet" in caplog.text


def test_create_sample_sheet(
    cli_runner: testing.CliRunner,
    flowcell_working_directory: Path,
    sample_sheet_context: dict,
    mocker,
):
    # GIVEN a flowcell directory with some run parameters
    flowcell: Flowcell = Flowcell(flowcell_working_directory)
    assert flowcell.run_parameters_path.exists()
    # GIVEN that there is no sample sheet present
    assert not flowcell.sample_sheet_exists()
    mocker.patch(
        "cg.apps.lims.samplesheet.flowcell_samples",
    )
    # GIVEN a lims api that returns some samples

    # WHEN creating a sample sheet
    cli_runner.invoke(
        create_sample_sheet, str(flowcell_working_directory), obj=sample_sheet_context
    )

    # THEN assert that the sample sheet was created
    assert flowcell.sample_sheet_exists()
