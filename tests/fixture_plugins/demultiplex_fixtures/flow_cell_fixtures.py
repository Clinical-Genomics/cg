"""Fixtures for flow cell objects."""

from pathlib import Path

import pytest

from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData

# Functional flow cell runs


@pytest.fixture(scope="module")
def hiseq_x_single_index_flow_cell(
    hiseq_x_single_index_flow_cell_dir: Path,
) -> FlowCellDirectoryData:
    """Return a single-index HiSeqX flow cell."""
    return FlowCellDirectoryData(flow_cell_path=hiseq_x_single_index_flow_cell_dir)


@pytest.fixture(scope="module")
def hiseq_x_dual_index_flow_cell(
    hiseq_x_dual_index_flow_cell_dir: Path,
) -> FlowCellDirectoryData:
    """Return a dual-index HiSeqX flow cell."""
    return FlowCellDirectoryData(flow_cell_path=hiseq_x_dual_index_flow_cell_dir)


@pytest.fixture(scope="module")
def hiseq_2500_dual_index_flow_cell(
    hiseq_2500_dual_index_flow_cell_dir: Path,
) -> FlowCellDirectoryData:
    """Return a dual-index HiSeq2500 flow cell."""
    return FlowCellDirectoryData(flow_cell_path=hiseq_2500_dual_index_flow_cell_dir)


@pytest.fixture(scope="module")
def hiseq_2500_custom_index_flow_cell(
    hiseq_2500_custom_index_flow_cell_dir: Path,
) -> FlowCellDirectoryData:
    """Return a custom-index HiSeq2500 flow cell."""
    return FlowCellDirectoryData(flow_cell_path=hiseq_2500_custom_index_flow_cell_dir)


@pytest.fixture()
def novaseq_6000_pre_1_5_kits_flow_cell(flow_cells_dir: Path) -> FlowCellDirectoryData:
    """Return a Novaseq6000 flow cell with index settings pre 1.5 kits."""
    return FlowCellDirectoryData(Path(flow_cells_dir, "190927_A00689_0069_BHLYWYDSXX"))


@pytest.fixture()
def novaseq_6000_pre_1_5_kits_flow_cell_bcl2fastq(flow_cells_dir: Path) -> FlowCellDirectoryData:
    """Return a Novaseq6000 flow cell with index settings pre 1.5 kits set as Bcl2Fastq."""
    return FlowCellDirectoryData(
        Path(flow_cells_dir, "190927_A00689_0069_BHLYWYDSXX"), bcl_converter=BclConverter.BCL2FASTQ
    )


@pytest.fixture()
def novaseq_6000_post_1_5_kits_flow_cell(flow_cells_dir: Path) -> FlowCellDirectoryData:
    """Return a Novaseq6000 flow cell with index settings post 1.5 kits."""
    return FlowCellDirectoryData(Path(flow_cells_dir, "230912_A00187_1009_AHK33MDRX3"))


@pytest.fixture()
def novaseq_x_flow_cell(novaseq_x_flow_cell_dir: Path) -> FlowCellDirectoryData:
    """Return a NovaSeqX flow cell."""
    return FlowCellDirectoryData(novaseq_x_flow_cell_dir)


# Demultiplexed runs


@pytest.fixture()
def novaseqx_flow_cell_with_sample_sheet_no_fastq(
    novaseqx_flow_cell_directory: Path, novaseqx_demultiplexed_flow_cell: Path
) -> FlowCellDirectoryData:
    """Return a flow cell from a tmp dir with a sample sheet and no sample fastq files."""
    novaseqx_flow_cell_directory.mkdir(parents=True, exist_ok=True)
    flow_cell = FlowCellDirectoryData(novaseqx_flow_cell_directory)
    sample_sheet_path = Path(
        novaseqx_demultiplexed_flow_cell, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
    )
    flow_cell._sample_sheet_path_hk = sample_sheet_path
    return flow_cell


@pytest.fixture
def tmp_bcl2fastq_flow_cell(
    tmp_demultiplexed_runs_bcl2fastq_directory: Path,
) -> FlowCellDirectoryData:
    """Create a flow cell object with flow cell that is demultiplexed."""
    return FlowCellDirectoryData(
        flow_cell_path=tmp_demultiplexed_runs_bcl2fastq_directory,
        bcl_converter=BclConverter.BCL2FASTQ,
    )


@pytest.fixture
def tmp_bcl_convert_flow_cell(
    tmp_flow_cell_directory_bclconvert: Path,
) -> FlowCellDirectoryData:
    """Create a flow cell object with flow cell that is demultiplexed."""
    return FlowCellDirectoryData(
        flow_cell_path=tmp_flow_cell_directory_bclconvert,
        bcl_converter=BclConverter.BCLCONVERT,
    )


@pytest.fixture
def unfinished_bcl2fastq_flow_cell(
    demultiplexed_runs_unfinished_bcl2fastq_flow_cell_directory: Path,
) -> FlowCellDirectoryData:
    """Copy the content of a demultiplexed but not finished directory to a temporary location."""
    return FlowCellDirectoryData(
        flow_cell_path=demultiplexed_runs_unfinished_bcl2fastq_flow_cell_directory,
        bcl_converter=BclConverter.BCL2FASTQ,
    )


# Flow cell attributes


@pytest.fixture
def bcl2fastq_flow_cell_id(
    novaseq_6000_pre_1_5_kits_flow_cell_bcl2fastq: FlowCellDirectoryData,
) -> str:
    """Return flow cell id from bcl2fastq flow cell object."""
    return novaseq_6000_pre_1_5_kits_flow_cell_bcl2fastq.id


@pytest.fixture
def bcl_convert_flow_cell_id(novaseq_6000_post_1_5_kits_flow_cell: FlowCellDirectoryData) -> str:
    """Return flow cell id from bcl_convert flow cell object."""
    return novaseq_6000_post_1_5_kits_flow_cell.id
