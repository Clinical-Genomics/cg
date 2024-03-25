from pathlib import Path

from _pytest.logging import LogCaptureFixture

from cg.apps.demultiplex.sample_sheet.api import SampleSheetAPI
from cg.models.cg_config import CGConfig
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData


def test_is_sample_sheet_from_flow_cell_translatable_passes(
    sample_sheet_context_broken_flow_cells: CGConfig,
    tmp_flow_cell_with_bcl2fastq_sample_sheet: Path,
):
    """Test that a flow cell with a translatable sample sheet is detected as translatable."""
    # GIVEN a sample sheet api
    api: SampleSheetAPI = sample_sheet_context_broken_flow_cells.sample_sheet_api

    # GIVEN a flow cell with a translatable sample sheet
    flow_cell = FlowCellDirectoryData(flow_cell_path=tmp_flow_cell_with_bcl2fastq_sample_sheet)

    # WHEN checking if the sample sheet is translatable
    result: bool = api._is_sample_sheet_from_flow_cell_translatable(flow_cell=flow_cell)

    # THEN assert that the sample sheet is translatable
    assert result


def test_is_sample_sheet_from_flow_cell_translatable_no_run_params(
    sample_sheet_context_broken_flow_cells: CGConfig,
    tmp_flow_cell_without_run_parameters_path: Path,
    caplog: LogCaptureFixture,
):
    """Test that a flow cell without run parameters can't have its sample sheet translated."""
    # GIVEN a sample sheet api
    api: SampleSheetAPI = sample_sheet_context_broken_flow_cells.sample_sheet_api

    # GIVEN a flow cell without run parameters
    flow_cell = FlowCellDirectoryData(flow_cell_path=tmp_flow_cell_without_run_parameters_path)

    # WHEN checking if the sample sheet is translatable
    result: bool = api._is_sample_sheet_from_flow_cell_translatable(flow_cell=flow_cell)

    # THEN assert that the sample sheet is not translatable
    assert not result
    assert f"Run parameters file for flow cell {flow_cell.full_name} does not exist" in caplog.text


def test_is_sample_sheet_from_flow_cell_translatable_no_sample_sheet(
    sample_sheet_context_broken_flow_cells: CGConfig,
    tmp_novaseq_x_without_sample_sheet_flow_cell_path: Path,
    caplog: LogCaptureFixture,
):
    """Test that a flow cell without sample sheet can't translate the sample sheet."""
    # GIVEN a sample sheet api
    api: SampleSheetAPI = sample_sheet_context_broken_flow_cells.sample_sheet_api

    # GIVEN a flow cell without a sample sheet
    flow_cell = FlowCellDirectoryData(
        flow_cell_path=tmp_novaseq_x_without_sample_sheet_flow_cell_path
    )

    # WHEN checking if the sample sheet is translatable
    result: bool = api._is_sample_sheet_from_flow_cell_translatable(flow_cell=flow_cell)

    # THEN assert that the sample sheet is not translatable
    assert not result
    assert f"Sample sheet for flow cell {flow_cell.full_name} does not exist" in caplog.text


def test_is_sample_sheet_from_flow_cell_translatable_bcl_convert_sample_sheet(
    sample_sheet_context: CGConfig,
    hiseq_2500_dual_index_flow_cell: FlowCellDirectoryData,
    caplog: LogCaptureFixture,
):
    """Test that a flow cell with a BCLConvert sample sheet can't translate it."""
    # GIVEN a sample sheet api
    api: SampleSheetAPI = sample_sheet_context.sample_sheet_api

    # GIVEN a flow cell with a BCLConvert sample sheet

    # WHEN checking if the sample sheet is translatable
    result: bool = api._is_sample_sheet_from_flow_cell_translatable(
        flow_cell=hiseq_2500_dual_index_flow_cell
    )

    # THEN assert that the sample sheet is not translatable
    assert not result
    assert (
        f"Sample sheet for flow cell {hiseq_2500_dual_index_flow_cell.full_name} is not a Bcl2Fastq sample sheet"
        in caplog.text
    )
