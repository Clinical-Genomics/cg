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
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.meta.demultiplex.housekeeper_storage_functions import get_sample_sheets_from_latest_version
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData

FLOW_CELL_FUNCTION_NAME: str = "cg.cli.demultiplex.sample_sheet.get_flow_cell_samples"


def test_create_sample_sheet_no_run_parameters_fails(
    cli_runner: testing.CliRunner,
    tmp_flow_cells_directory_no_run_parameters: Path,
    sample_sheet_context: CGConfig,
    lims_novaseq_bcl2fastq_samples: List[FlowCellSampleNovaSeq6000Bcl2Fastq],
    caplog,
    mocker,
):
    """Test that creating a flow cell sample sheet fails if there is no run parameters file."""
    # GIVEN a folder with a non-existing sample sheet nor RunParameters file
    flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=tmp_flow_cells_directory_no_run_parameters
    )
    assert not flow_cell.run_parameters_path.exists()

    # GIVEN flow cell samples
    mocker.patch(
        FLOW_CELL_FUNCTION_NAME,
        return_value=lims_novaseq_bcl2fastq_samples,
    )

    # GIVEN that the context's flow cell directory holds the given flow cell
    sample_sheet_context.flow_cells_dir: str = (
        tmp_flow_cells_directory_no_run_parameters.parent.as_posix()
    )

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
    """Test that creating a Bcl2fastq sample sheet works."""
    # GIVEN a flowcell directory with some run parameters
    flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=tmp_flow_cells_directory_no_sample_sheet,
        bcl_converter=BclConverter.BCL2FASTQ,
    )
    assert flow_cell.run_parameters_path.exists()

    # GIVEN that there is no sample sheet in the flow cell dir
    assert not flow_cell.sample_sheet_exists()

    # GIVEN that there are no sample sheet in Housekeeper
    assert not get_sample_sheets_from_latest_version(
        flow_cell_id=flow_cell.id, hk_api=sample_sheet_context.housekeeper_api
    )

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
    assert flow_cell.sample_sheet_exists()

    # THEN the sample sheet is on the correct format
    assert flow_cell.validate_sample_sheet()

    # THEN the sample sheet is in Housekeeper
    assert get_sample_sheets_from_latest_version(
        flow_cell_id=flow_cell.id, hk_api=sample_sheet_context.housekeeper_api
    )


def test_create_dragen_sample_sheet(
    cli_runner: testing.CliRunner,
    tmp_flow_cells_directory_no_sample_sheet: Path,
    sample_sheet_context: CGConfig,
    lims_novaseq_bcl_convert_samples: List[FlowCellSampleNovaSeq6000Dragen],
    mocker,
):
    """Test that creating a Dragen sample sheet works."""
    # GIVEN a flow cell directory with some run parameters
    flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        tmp_flow_cells_directory_no_sample_sheet, bcl_converter=BclConverter.DRAGEN
    )
    assert flow_cell.run_parameters_path.exists()

    # GIVEN that there is no sample sheet in the flow cell dir
    assert not flow_cell.sample_sheet_exists()

    # GIVEN that there are no sample sheet in Housekeeper
    assert not get_sample_sheets_from_latest_version(
        flow_cell_id=flow_cell.id, hk_api=sample_sheet_context.housekeeper_api
    )

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

    # THEN the sample sheet is in Housekeeper
    assert get_sample_sheets_from_latest_version(
        flow_cell_id=flow_cell.id, hk_api=sample_sheet_context.housekeeper_api
    )
