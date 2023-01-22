from pathlib import Path
from typing import List

from click import testing

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.lims.samplesheet import (
    LimsFlowcellSample,
    LimsFlowcellSampleBcl2Fastq,
    LimsFlowcellSampleDragen,
)
from cg.cli.demultiplex.sample_sheet import create_sheet
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCell


def test_create_sample_sheet_no_run_parameters(
    cli_runner: testing.CliRunner,
    flow_cell_working_directory_no_run_parameters: Path,
    sample_sheet_context: CGConfig,
    caplog,
    mocker,
):
    # GIVEN a folder with a non existing sample sheet
    flowcell_object: FlowCell = FlowCell(flow_cell_working_directory_no_run_parameters)
    assert flowcell_object.run_parameters_path.exists() is False
    mocker.patch("cg.cli.demultiplex.sample_sheet.flowcell_samples", return_value=[{"sample": 1}])
    demux_api: DemultiplexingAPI = sample_sheet_context.demultiplex_api
    demux_api.run_dir = flow_cell_working_directory_no_run_parameters.parent
    sample_sheet_context.demultiplex_api_ = demux_api

    # WHEN running the create sample sheet command
    result: testing.Result = cli_runner.invoke(
        create_sheet, [flowcell_object.full_name], obj=sample_sheet_context
    )

    # THEN assert it exits with a non zero exit code
    assert result.exit_code != 0
    # THEN assert the correct information is communicated
    assert "Could not find run parameters file" in caplog.text


def test_create_bcl2fastq_sample_sheet(
    cli_runner: testing.CliRunner,
    flow_cell_working_directory: Path,
    sample_sheet_context: CGConfig,
    lims_novaseq_bcl2fastq_samples: List[LimsFlowcellSampleBcl2Fastq],
    mocker,
):
    # GIVEN a flowcell directory with some run parameters
    flowcell: FlowCell = FlowCell(flow_cell_working_directory)
    assert flowcell.run_parameters_path.exists()
    # GIVEN that there is no sample sheet present
    assert not flowcell.sample_sheet_exists()
    mocker.patch(
        "cg.cli.demultiplex.sample_sheet.flowcell_samples",
        return_value=lims_novaseq_bcl2fastq_samples,
    )
    # GIVEN a lims api that returns some samples

    # WHEN creating a sample sheet
    result = cli_runner.invoke(
        create_sheet, [str(flow_cell_working_directory)], obj=sample_sheet_context
    )

    # THEN assert it exits with success
    assert result.exit_code == 0
    # THEN assert that the sample sheet was created
    assert flowcell.sample_sheet_exists()
    # THEN assert that the sample sheet is on the correct format
    assert flowcell.validate_sample_sheet()


def test_create_dragen_sample_sheet(
    cli_runner: testing.CliRunner,
    flow_cell_working_directory: Path,
    sample_sheet_context: CGConfig,
    lims_novaseq_dragen_samples: List[LimsFlowcellSampleDragen],
    mocker,
):
    # GIVEN a flowcell directory with some run parameters
    flowcell: FlowCell = FlowCell(flow_cell_working_directory, bcl_converter="dragen")
    assert flowcell.run_parameters_path.exists()
    # GIVEN that there is no sample sheet present
    assert not flowcell.sample_sheet_exists()
    mocker.patch(
        "cg.cli.demultiplex.sample_sheet.flowcell_samples",
        return_value=lims_novaseq_dragen_samples,
    )
    # GIVEN a lims api that returns some samples

    # WHEN creating a sample sheet
    result = cli_runner.invoke(
        create_sheet, [str(flow_cell_working_directory), "-b", "dragen"], obj=sample_sheet_context
    )

    # THEN assert it exits with success
    assert result.exit_code == 0
    # THEN assert that the sample sheet was created
    assert flowcell.sample_sheet_exists()
    # THEN assert that the sample sheet is on the correct format
    assert flowcell.validate_sample_sheet()
