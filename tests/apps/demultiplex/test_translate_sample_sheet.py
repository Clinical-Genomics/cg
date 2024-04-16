from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture

from cg.apps.demultiplex.sample_sheet.api import SampleSheetAPI
from cg.exc import SampleSheetError
from cg.models.cg_config import CGConfig
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData


@pytest.mark.parametrize(
    "context, flow_cell_path, expected_result",
    [
        ("sample_sheet_context", "novaseq_6000_post_1_5_kits_flow_cell_path", False),
        (
            "sample_sheet_context_broken_flow_cells",
            "tmp_flow_cell_with_bcl2fastq_sample_sheet",
            True,
        ),
    ],
    ids=["BCLConvert", "BCL2FASTQ"],
)
def test_is_sample_sheet_bcl2fastq(
    context: str, flow_cell_path: str, expected_result: bool, request: FixtureRequest
):
    """Test that sample sheets type BCL2FASTQ return True, and type BCLConvert return False."""
    # GIVEN a sample sheet API
    context: CGConfig = request.getfixturevalue(context)
    api: SampleSheetAPI = context.sample_sheet_api

    # GIVEN a flow cell with a sample sheet
    flow_cell_path: Path = request.getfixturevalue(flow_cell_path)
    flow_cell = FlowCellDirectoryData(flow_cell_path=flow_cell_path)

    # WHEN checking if the sample sheet is a BCL2FASTQ
    result: bool = api._is_sample_sheet_bcl2fastq(flow_cell=flow_cell)

    # THEN assert that the sample sheet is detected correctly
    assert result == expected_result


def test_is_sample_sheet_from_flow_cell_translatable_passes(
    sample_sheet_context_broken_flow_cells: CGConfig,
    tmp_flow_cell_with_bcl2fastq_sample_sheet: Path,
):
    """Test that a flow cell with a translatable sample sheet is detected as translatable."""
    # GIVEN a sample sheet API
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
    # GIVEN a sample sheet API
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
    """Test that a flow cell without sample sheet can not be translated."""
    # GIVEN a sample sheet API
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
    """Test that a flow cell with a BCLConvert sample sheet can not be translated."""
    # GIVEN a sample sheet API
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


def test_replace_sample_sheet_header_bcl2fastq(
    sample_sheet_context: CGConfig,
    sample_sheet_bcl2fastq_data_header: list[list[str]],
    sample_sheet_bcl2fastq_data_header_with_replaced_sample_id: list[list[str]],
):
    """Test that the header is replaced to BCLConvert format for a Bcl2Fastq sample sheet."""
    # GIVEN a sample sheet API
    api: SampleSheetAPI = sample_sheet_context.sample_sheet_api

    # GIVEN a Bcl2Fastq sample sheet content

    # WHEN replacing the data header
    new_content: list[list[str]] = api._replace_sample_header(sample_sheet_bcl2fastq_data_header)

    # THEN the new header has BCLConvert column names
    assert new_content == sample_sheet_bcl2fastq_data_header_with_replaced_sample_id


def test_replace_sample_sheet_header_bcl_convert(
    sample_sheet_context: CGConfig,
    sample_sheet_bcl2fastq_data_header_with_replaced_sample_id: list[list[str]],
):
    """Test that the header of a BCLConvert sample sheet can not be replaced."""
    # GIVEN a sample sheet API
    api: SampleSheetAPI = sample_sheet_context.sample_sheet_api

    # GIVEN a BCLConvert sample sheet content

    # WHEN replacing the header
    with pytest.raises(SampleSheetError) as error:
        # THEN an error is raised
        api._replace_sample_header(sample_sheet_bcl2fastq_data_header_with_replaced_sample_id)
    assert "Could not find data header in sample sheet" in str(error.value)


def test_translate_sample_sheet(
    sample_sheet_context_broken_flow_cells: CGConfig,
    tmp_flow_cell_with_bcl2fastq_sample_sheet: Path,
):
    """Test that a Bcl2Fastq sample sheet is translated to BCLConvert format."""
    # GIVEN a sample sheet API
    api: SampleSheetAPI = sample_sheet_context_broken_flow_cells.sample_sheet_api

    # GIVEN a flow cell with a translatable sample sheet
    flow_cell = FlowCellDirectoryData(flow_cell_path=tmp_flow_cell_with_bcl2fastq_sample_sheet)

    # WHEN translating the sample sheet
    api.translate_sample_sheet(flow_cell_name=flow_cell.full_name)

    # THEN the sample sheet is translated correctly to BCConvert format
    api.validate_sample_sheet(flow_cell.sample_sheet_path)
