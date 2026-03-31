from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, create_autospec

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

from cg.apps.demultiplex.sample_sheet.api import IlluminaSampleSheetService
from cg.apps.demultiplex.sample_sheet.sample_models import IlluminaSampleIndexSetting
from cg.exc import HousekeeperFileMissingError
from cg.models.cg_config import CGConfig
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from tests.store_helpers import StoreHelpers

GET_FLOW_CELL_SAMPLES: str = "cg.apps.demultiplex.sample_sheet.api.get_flow_cell_samples"


def test_get_create_sample_sheet_hk_has_bcl2fastq_sample_sheet(
    sample_sheet_context_broken_flow_cells: CGConfig,
    tmp_flow_cell_with_bcl2fastq_sample_sheet: Path,
    sample_sheet_bcl2fastq_bundle_data: dict[str, Any],
    hiseq_x_single_index_bcl_convert_lims_samples: list[IlluminaSampleIndexSetting],
    helpers: StoreHelpers,
    mocker: MockFixture,
):
    """Test that a BCL2FASTQ sample sheet in Housekeeper is updated to BCLConvert."""
    # GIVEN a sample sheet context with a sample sheet API and a Housekeeper API
    sample_sheet_api = sample_sheet_context_broken_flow_cells.sample_sheet_api
    hk_api = sample_sheet_context_broken_flow_cells.housekeeper_api

    # GIVEN a a flow cell with a BCL2FASTQ sample sheet going to be updated to BCLConvert
    flow_cell = IlluminaRunDirectoryData(tmp_flow_cell_with_bcl2fastq_sample_sheet)

    # GIVEN that the sample sheet is in Housekeeper
    helpers.ensure_hk_bundle(store=hk_api, bundle_data=sample_sheet_bcl2fastq_bundle_data)
    sample_sheet_path_hk: Path = hk_api.get_sample_sheet_path(flow_cell.id)

    # GIVEN that the flow cell samples are in LIMS
    mocker.patch(
        GET_FLOW_CELL_SAMPLES,
        return_value=hiseq_x_single_index_bcl_convert_lims_samples,
    )

    # WHEN getting the sample sheet in BCLConvert format
    sample_sheet_api.get_or_create_sample_sheet(flow_cell.full_name)

    # THEN the sample sheet in Housekeeper is replaced with the BCLConvert sample sheet
    sample_sheet_api.validate_sample_sheet(sample_sheet_path_hk)

    # THEN the sample sheet in the flow cell is replaced with the BCLConvert sample sheet
    sample_sheet_api.validate_sample_sheet(flow_cell.sample_sheet_path)


def test_get_create_sample_sheet_flow_cell_has_bcl2fastq_sample_sheet(
    sample_sheet_context_broken_flow_cells: CGConfig,
    tmp_flow_cell_with_bcl2fastq_sample_sheet: Path,
    hiseq_x_single_index_bcl_convert_lims_samples: list[IlluminaSampleIndexSetting],
    mocker: MockFixture,
    caplog: LogCaptureFixture,
):
    """
    Test that a BCL2FASTQ sample sheet in the flow cell directory is updated to BCLConvert
    and added to Housekeeeper.
    """
    # GIVEN a sample sheet context with a sample sheet API and a Housekeeper API
    sample_sheet_api = sample_sheet_context_broken_flow_cells.sample_sheet_api
    hk_api = sample_sheet_context_broken_flow_cells.housekeeper_api

    # GIVEN a a flow cell with a BCL2FASTQ sample sheet going to be updated to BCLConvert
    flow_cell = IlluminaRunDirectoryData(tmp_flow_cell_with_bcl2fastq_sample_sheet)

    # GIVEN that the sample sheet is not in Housekeeper
    with pytest.raises(HousekeeperFileMissingError):
        hk_api.get_sample_sheet_path(flow_cell.id)
    assert f"Sample sheet file for flowcell {flow_cell.id} not found in Housekeeper!" in caplog.text

    # GIVEN that the flow cell samples are in LIMS
    mocker.patch(
        GET_FLOW_CELL_SAMPLES,
        return_value=hiseq_x_single_index_bcl_convert_lims_samples,
    )

    # WHEN getting the sample sheet in BCLConvert format
    sample_sheet_api.get_or_create_sample_sheet(flow_cell.full_name)

    # THEN the sample sheet has been added to Housekeeper and passes BCLConvert validation
    sample_sheet_path_hk: Path = hk_api.get_sample_sheet_path(flow_cell.id)
    sample_sheet_api.validate_sample_sheet(sample_sheet_path_hk)

    # THEN the sample sheet in the flow cell directory is replaced with the BCLConvert sample sheet
    sample_sheet_api.validate_sample_sheet(flow_cell.sample_sheet_path)


def test_get_or_create_sample_sheet_skips_on_instrument_demuxed_runs(
    sample_sheet_context_broken_flow_cells: CGConfig,
    novaseq_x_flow_cell_full_name: str,
    mocker: MockFixture,
):
    """Test that get_or_create_sample_sheet returns early for on-instrument demuxed runs."""
    # GIVEN a sample sheet API
    sample_sheet_api: IlluminaSampleSheetService = (
        sample_sheet_context_broken_flow_cells.sample_sheet_api
    )

    # GIVEN a flow cell that was demultiplexed on the sequencer
    mock_flow_cell: IlluminaRunDirectoryData = create_autospec(IlluminaRunDirectoryData)
    mock_flow_cell.has_demultiplexing_started_on_sequencer = Mock(return_value=True)
    mocker.patch.object(sample_sheet_api, "_get_flow_cell", return_value=mock_flow_cell)

    # GIVEN that sample sheet creation is tracked
    mock_create: MagicMock = mocker.patch.object(sample_sheet_api, "_create_sample_sheet_file")

    # WHEN getting or creating the sample sheet
    sample_sheet_api.get_or_create_sample_sheet(novaseq_x_flow_cell_full_name)

    # THEN no sample sheet was created
    mock_create.assert_not_called()
