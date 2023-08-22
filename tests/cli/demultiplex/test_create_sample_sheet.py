from pathlib import Path
from typing import List

from click import testing

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSampleNovaSeq6000Bcl2Fastq,
    FlowCellSampleNovaSeq6000Dragen,
)
from cg.cli.demultiplex.sample_sheet import create_sheet
from cg.constants.demultiplexing import BclConverter
from cg.constants.process import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData

FLOW_CELL_FUNCTION_NAME: str = "cg.cli.demultiplex.sample_sheet.get_flow_cell_samples"


def test_create_sample_sheet_no_run_parameters(
    cli_runner: testing.CliRunner,
    tmp_flow_cells_directory_no_run_parameters: Path,
    sample_sheet_context: CGConfig,
    lims_novaseq_bcl2fastq_samples: List[FlowCellSampleNovaSeq6000Bcl2Fastq],
    caplog,
    mocker,
):
    # GIVEN a folder with a non-existing sample sheet
    flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=tmp_flow_cells_directory_no_run_parameters
    )
    assert not flow_cell.run_parameters_path.exists()

    # GIVEN flow cell samples
    mocker.patch(
        FLOW_CELL_FUNCTION_NAME,
        return_value=lims_novaseq_bcl2fastq_samples,
    )

    # GIVEN a demux API context
    demux_api: DemultiplexingAPI = sample_sheet_context.demultiplex_api
    demux_api.flow_cells_dir: Path = tmp_flow_cells_directory_no_run_parameters.parent
    sample_sheet_context.demultiplex_api_: DemultiplexingAPI = demux_api

    # WHEN running the create sample sheet command
    result: testing.Result = cli_runner.invoke(
        create_sheet, [flow_cell.full_name], obj=sample_sheet_context
    )

    # THEN the process exits with a non-zero exit code
    assert result.exit_code != EXIT_SUCCESS

    # THEN the correct information is communicated
    assert "Could not find run parameters file" in caplog.text


def test_create_bcl2fastq_sample_sheet(
    cli_runner: testing.CliRunner,
    tmp_flow_cells_directory_no_sample_sheet: Path,
    sample_sheet_context: CGConfig,
    lims_novaseq_bcl2fastq_samples: List[FlowCellSampleNovaSeq6000Bcl2Fastq],
    mocker,
):
    # GIVEN a flowcell directory with some run parameters
    flowcell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=tmp_flow_cells_directory_no_sample_sheet,
        bcl_converter=BclConverter.BCL2FASTQ,
    )
    assert flowcell.run_parameters_path.exists()

    # GIVEN that there is no sample sheet present
    assert not flowcell.sample_sheet_exists()

    # GIVEN flow cell samples
    mocker.patch(
        FLOW_CELL_FUNCTION_NAME,
        return_value=lims_novaseq_bcl2fastq_samples,
    )
    # GIVEN a lims api that returns some samples

    # WHEN creating a sample sheet
    result = cli_runner.invoke(
        create_sheet,
        [str(tmp_flow_cells_directory_no_sample_sheet), "--bcl-converter", "bcl2fastq"],
        obj=sample_sheet_context,
    )

    # THEN the process finishes successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the sample sheet was created
    assert flowcell.sample_sheet_exists()

    # THEN the sample sheet is on the correct format
    assert flowcell.validate_sample_sheet()


def test_create_dragen_sample_sheet(
    cli_runner: testing.CliRunner,
    tmp_flow_cells_directory_no_sample_sheet: Path,
    sample_sheet_context: CGConfig,
    lims_novaseq_bcl_convert_samples: List[FlowCellSampleNovaSeq6000Dragen],
    mocker,
):
    # GIVEN a flow cell directory with some run parameters
    flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        tmp_flow_cells_directory_no_sample_sheet, bcl_converter=BclConverter.DRAGEN
    )
    assert flow_cell.run_parameters_path.exists()

    # GIVEN that there is no sample sheet present
    assert not flow_cell.sample_sheet_exists()

    # GIVEN flow cell samples
    mocker.patch(
        FLOW_CELL_FUNCTION_NAME,
        return_value=lims_novaseq_bcl_convert_samples,
    )
    # GIVEN a LIMS API that returns samples

    # WHEN creating a sample sheet
    result = cli_runner.invoke(
        create_sheet,
        [str(tmp_flow_cells_directory_no_sample_sheet), "-b", BclConverter.DRAGEN],
        obj=sample_sheet_context,
    )

    # THEN the process finishes successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the sample sheet was created
    assert flow_cell.sample_sheet_exists()

    # THEN the sample sheet is on the correct format
    assert flow_cell.validate_sample_sheet()
