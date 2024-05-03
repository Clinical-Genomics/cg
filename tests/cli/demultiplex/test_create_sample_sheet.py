from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest
from click.testing import CliRunner, Result
from pydantic import BaseModel

from cg.apps.demultiplex.sample_sheet.api import SampleSheetAPI
from cg.apps.demultiplex.sample_sheet.sample_models import FlowCellSample
from cg.cli.demultiplex.sample_sheet import create_sheet
from cg.constants.process import EXIT_SUCCESS
from cg.io.txt import read_txt
from cg.models.cg_config import CGConfig
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData

GET_FLOW_CELL_SAMPLES: str = "cg.apps.demultiplex.sample_sheet.api.get_flow_cell_samples"


def test_create_sample_sheet_no_run_parameters_fails(
    cli_runner: CliRunner,
    tmp_flow_cell_without_run_parameters_path: Path,
    sample_sheet_context_broken_flow_cells: CGConfig,
    hiseq_2500_custom_index_bcl_convert_lims_samples: list[FlowCellSample],
    caplog,
    mocker,
):
    """Test that creating a flow cell sample sheet fails if there is no run parameters file."""
    # GIVEN a flow cell directory with a non-existing sample sheet nor RunParameters file
    flow_cell = FlowCellDirectoryData(tmp_flow_cell_without_run_parameters_path)

    # GIVEN that the context's flow cell directory holds the given flow cell
    assert (
        sample_sheet_context_broken_flow_cells.illumina_demultiplexed_runs_directory
        == flow_cell.path.parent.as_posix()
    )

    # GIVEN flow cell samples
    mocker.patch(
        GET_FLOW_CELL_SAMPLES,
        return_value=hiseq_2500_custom_index_bcl_convert_lims_samples,
    )

    # WHEN running the create sample sheet command
    result: Result = cli_runner.invoke(
        create_sheet, [flow_cell.full_name], obj=sample_sheet_context_broken_flow_cells
    )

    # THEN the process exits with a non-zero exit code
    assert result.exit_code != EXIT_SUCCESS

    # THEN the correct information is communicated
    assert "No run parameters file found in flow cell" in caplog.text


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
    cli_runner: CliRunner,
    scenario: SampleSheetScenario,
    sample_sheet_context: CGConfig,
    mocker,
    request: FixtureRequest,
):
    """Test that creating a v2 sample sheet works."""
    # GIVEN a sample sheet context with a sample sheet api
    sample_sheet_api: SampleSheetAPI = sample_sheet_context.sample_sheet_api

    # GIVEN a flow cell directory with some run parameters
    flow_cell_directory: Path = request.getfixturevalue(scenario.flow_cell_directory)
    flow_cell = FlowCellDirectoryData(flow_cell_directory)
    assert flow_cell.run_parameters_path.exists()

    # GIVEN that there is no sample sheet in the flow cell dir
    assert not flow_cell.sample_sheet_exists()

    # GIVEN that there are no sample sheet in Housekeeper
    assert not sample_sheet_context.housekeeper_api.get_sample_sheets_from_latest_version(
        flow_cell.id
    )

    # GIVEN flow cell samples
    mocker.patch(
        GET_FLOW_CELL_SAMPLES,
        return_value=request.getfixturevalue(scenario.lims_samples),
    )
    # GIVEN a LIMS API that returns samples

    # WHEN creating a sample sheet
    result: Result = cli_runner.invoke(
        create_sheet,
        [str(flow_cell_directory)],
        obj=sample_sheet_context,
    )

    # THEN the process finishes successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the sample sheet was created
    assert flow_cell.sample_sheet_exists()

    # THEN the sample sheet passes validation
    sample_sheet_api.validate_sample_sheet(flow_cell.sample_sheet_path)

    # THEN the sample sheet is in Housekeeper
    assert sample_sheet_context.housekeeper_api.get_sample_sheets_from_latest_version(flow_cell.id)

    # THEN the sample sheet should have the exact structure
    generated_content: str = read_txt(flow_cell.sample_sheet_path)
    correct_content: str = read_txt(Path(request.getfixturevalue(scenario.correct_sample_sheet)))
    assert generated_content == correct_content
