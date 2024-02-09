from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest
from click import testing
from pydantic import BaseModel

from cg.apps.demultiplex.sample_sheet.sample_models import (
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.cli.demultiplex.sample_sheet import create_sheet
from cg.constants.demultiplexing import BclConverter
from cg.constants.process import EXIT_SUCCESS
from cg.io.txt import read_txt
from cg.models.cg_config import CGConfig
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData

FLOW_CELL_FUNCTION_NAME: str = "cg.cli.demultiplex.sample_sheet.get_flow_cell_samples"


def test_create_sample_sheet_no_run_parameters_fails(
    cli_runner: testing.CliRunner,
    tmp_flow_cell_without_run_parameters_path: Path,
    sample_sheet_context: CGConfig,
    hiseq_2500_custom_index_bcl_convert_lims_samples: list[FlowCellSampleBcl2Fastq],
    caplog,
    mocker,
):
    """Test that creating a flow cell sample sheet fails if there is no run parameters file."""
    # GIVEN a folder with a non-existing sample sheet nor RunParameters file
    flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=tmp_flow_cell_without_run_parameters_path
    )

    # GIVEN flow cell samples
    mocker.patch(
        FLOW_CELL_FUNCTION_NAME,
        return_value=hiseq_2500_custom_index_bcl_convert_lims_samples,
    )

    # GIVEN that the context's flow cell directory holds the given flow cell
    sample_sheet_context.flow_cells_dir = (
        tmp_flow_cell_without_run_parameters_path.parent.as_posix()
    )

    # WHEN running the create sample sheet command
    result: testing.Result = cli_runner.invoke(
        create_sheet, [flow_cell.full_name], obj=sample_sheet_context
    )

    # THEN the process exits with a non-zero exit code
    assert result.exit_code != EXIT_SUCCESS

    # THEN the correct information is communicated
    assert "No run parameters file found in flow cell" in caplog.text


def test_create_bcl2fastq_sample_sheet(
    cli_runner: testing.CliRunner,
    tmp_novaseq_6000_pre_1_5_kits_flow_cell_without_sample_sheet_path: Path,
    sample_sheet_context: CGConfig,
    novaseq_6000_pre_1_5_kits_bcl2fastq_lims_samples: list[FlowCellSampleBcl2Fastq],
    mocker,
):
    """Test that creating a Bcl2fastq sample sheet works."""
    # GIVEN a flowcell directory with some run parameters
    flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=tmp_novaseq_6000_pre_1_5_kits_flow_cell_without_sample_sheet_path,
        bcl_converter=BclConverter.BCL2FASTQ,
    )
    assert flow_cell.run_parameters_path.exists()

    # GIVEN that there is no sample sheet in the flow cell dir
    assert not flow_cell.sample_sheet_exists()

    # GIVEN that there are no sample sheet in Housekeeper
    assert not sample_sheet_context.housekeeper_api.get_sample_sheets_from_latest_version(
        flow_cell.id
    )

    # GIVEN flow cell samples
    mocker.patch(
        FLOW_CELL_FUNCTION_NAME,
        return_value=novaseq_6000_pre_1_5_kits_bcl2fastq_lims_samples,
    )
    # GIVEN a lims api that returns some samples

    # WHEN creating a sample sheet
    result = cli_runner.invoke(
        create_sheet,
        [
            str(tmp_novaseq_6000_pre_1_5_kits_flow_cell_without_sample_sheet_path),
            "--bcl-converter",
            BclConverter.BCL2FASTQ,
        ],
        obj=sample_sheet_context,
    )

    # THEN the process finishes successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the sample sheet was created
    assert flow_cell.sample_sheet_exists()

    # THEN the sample sheet is on the correct format
    assert flow_cell.validate_sample_sheet()

    # THEN the sample sheet is in Housekeeper
    assert sample_sheet_context.housekeeper_api.get_sample_sheets_from_latest_version(flow_cell.id)


class SampleSheetScenario(BaseModel):
    flow_cell_directory: str
    lims_samples: str
    correct_sample_sheet: str


@pytest.mark.parametrize(
    "scenario",
    [
        SampleSheetScenario(
            flow_cell_directory="tmp_novaseq_6000_pre_1_5_kits_flow_cell_without_sample_sheet_path",
            lims_samples="novaseq_6000_pre_1_5_kits_bcl_convert_lims_samples",
            correct_sample_sheet="novaseq_6000_pre_1_5_kits_correct_sample_sheet_path",
        ),
        SampleSheetScenario(
            flow_cell_directory="tmp_novaseq_6000_post_1_5_kits_flow_cell_without_sample_sheet_path",
            lims_samples="novaseq_6000_post_1_5_kits_bcl_convert_lims_samples",
            correct_sample_sheet="novaseq_6000_post_1_5_kits_correct_sample_sheet_path",
        ),
        SampleSheetScenario(
            flow_cell_directory="tmp_novaseq_x_without_sample_sheet_flow_cell_path",
            lims_samples="novaseq_x_lims_samples",
            correct_sample_sheet="novaseq_x_correct_sample_sheet",
        ),
    ],
    ids=["Old NovaSeq 6000 flow cell", "New NovaSeq 6000 flow cell", "NovaSeq X flow cell"],
)
def test_create_v2_sample_sheet(
    cli_runner: testing.CliRunner,
    scenario: SampleSheetScenario,
    sample_sheet_context: CGConfig,
    mocker,
    request: FixtureRequest,
):
    """Test that creating a v2 sample sheet works."""
    flow_cell_directory: Path = request.getfixturevalue(scenario.flow_cell_directory)
    # GIVEN a flow cell directory with some run parameters
    flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(flow_cell_directory)
    assert flow_cell.run_parameters_path.exists()

    # GIVEN that there is no sample sheet in the flow cell dir
    assert not flow_cell.sample_sheet_exists()

    # GIVEN that there are no sample sheet in Housekeeper
    assert not sample_sheet_context.housekeeper_api.get_sample_sheets_from_latest_version(
        flow_cell.id
    )

    # GIVEN flow cell samples
    mocker.patch(
        FLOW_CELL_FUNCTION_NAME,
        return_value=request.getfixturevalue(scenario.lims_samples),
    )
    # GIVEN a LIMS API that returns samples

    # WHEN creating a sample sheet
    result = cli_runner.invoke(
        create_sheet,
        [str(flow_cell_directory), "-b", BclConverter.BCLCONVERT],
        obj=sample_sheet_context,
    )

    # THEN the process finishes successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the sample sheet was created
    assert flow_cell.sample_sheet_exists()

    # THEN the sample sheet is on the correct format
    assert flow_cell.validate_sample_sheet()

    # THEN the sample sheet is in Housekeeper
    assert sample_sheet_context.housekeeper_api.get_sample_sheets_from_latest_version(flow_cell.id)

    # THEN the sample sheet should have the exact structure
    generated_content: str = read_txt(flow_cell.sample_sheet_path)
    correct_content: str = read_txt(Path(request.getfixturevalue(scenario.correct_sample_sheet)))
    assert generated_content == correct_content


def test_incorrect_bcl2fastq_headers_samplesheet(
    cli_runner: testing.CliRunner,
    tmp_flow_cells_directory_malformed_sample_sheet: Path,
    sample_sheet_context: CGConfig,
    novaseq_6000_pre_1_5_kits_bcl2fastq_lims_samples: list[FlowCellSampleBcl2Fastq],
    mocker,
    caplog,
):
    """Test that correct logging is done when a Bcl2fastq generated sample sheet is malformed."""
    # GIVEN a flowcell directory with some run parameters
    flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=tmp_flow_cells_directory_malformed_sample_sheet,
        bcl_converter=BclConverter.BCL2FASTQ,
    )

    # GIVEN flow cell samples
    mocker.patch(
        FLOW_CELL_FUNCTION_NAME,
        return_value=novaseq_6000_pre_1_5_kits_bcl2fastq_lims_samples,
    )
    # GIVEN a lims api that returns some samples

    # WHEN creating a sample sheet
    cli_runner.invoke(
        create_sheet,
        [
            str(tmp_flow_cells_directory_malformed_sample_sheet),
            "--bcl-converter",
            BclConverter.BCL2FASTQ,
        ],
        obj=sample_sheet_context,
    )

    # THEN the sample sheet was created
    assert flow_cell.sample_sheet_exists()

    # THEN the sample sheet is not in the correct format
    assert not flow_cell.validate_sample_sheet()

    # THEN the expected headers should have been logged
    assert (
        "Ensure that the headers in the sample sheet follows the allowed structure for bcl2fastq"
        in caplog.text
    )

    assert (
        "FCID,Lane,SampleID,SampleRef,index,SampleName,Control,Recipe,Operator,Project"
        in caplog.text
    )
