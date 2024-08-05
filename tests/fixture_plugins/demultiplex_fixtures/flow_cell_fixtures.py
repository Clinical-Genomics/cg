"""Fixtures for Illumina flow cell objects."""

from pathlib import Path

import pytest

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData

# Canonical flow cell runs


@pytest.fixture(scope="module")
def hiseq_x_single_index_flow_cell(
    hiseq_x_single_index_flow_cell_dir: Path,
) -> IlluminaRunDirectoryData:
    """Return a single-index HiSeqX flow cell."""
    return IlluminaRunDirectoryData(sequencing_run_path=hiseq_x_single_index_flow_cell_dir)


@pytest.fixture(scope="module")
def hiseq_x_dual_index_flow_cell(
    hiseq_x_dual_index_flow_cell_dir: Path,
) -> IlluminaRunDirectoryData:
    """Return a dual-index HiSeqX flow cell."""
    return IlluminaRunDirectoryData(sequencing_run_path=hiseq_x_dual_index_flow_cell_dir)


@pytest.fixture(scope="module")
def hiseq_2500_dual_index_flow_cell(
    hiseq_2500_dual_index_flow_cell_dir: Path,
) -> IlluminaRunDirectoryData:
    """Return a dual-index HiSeq2500 flow cell."""
    return IlluminaRunDirectoryData(sequencing_run_path=hiseq_2500_dual_index_flow_cell_dir)


@pytest.fixture(scope="module")
def hiseq_2500_custom_index_flow_cell(
    hiseq_2500_custom_index_flow_cell_dir: Path,
) -> IlluminaRunDirectoryData:
    """Return a custom-index HiSeq2500 flow cell."""
    return IlluminaRunDirectoryData(sequencing_run_path=hiseq_2500_custom_index_flow_cell_dir)


@pytest.fixture
def novaseq_6000_pre_1_5_kits_flow_cell(
    illumina_sequencing_runs_directory: Path,
    novaseq_6000_pre_1_5_kits_flow_cell_full_name: str,
) -> IlluminaRunDirectoryData:
    """Return a Novaseq6000 flow cell with index settings pre 1.5 kits."""
    return IlluminaRunDirectoryData(
        Path(illumina_sequencing_runs_directory, novaseq_6000_pre_1_5_kits_flow_cell_full_name)
    )


@pytest.fixture
def novaseq_6000_post_1_5_kits_flow_cell(
    illumina_sequencing_runs_directory: Path,
    novaseq_6000_post_1_5_kits_flow_cell_full_name: str,
) -> IlluminaRunDirectoryData:
    """Return a Novaseq6000 flow cell with index settings post 1.5 kits."""
    return IlluminaRunDirectoryData(
        Path(illumina_sequencing_runs_directory, novaseq_6000_post_1_5_kits_flow_cell_full_name)
    )


@pytest.fixture
def novaseq_x_flow_cell(novaseq_x_flow_cell_dir: Path) -> IlluminaRunDirectoryData:
    """Return a NovaSeqX flow cell."""
    return IlluminaRunDirectoryData(novaseq_x_flow_cell_dir)


@pytest.fixture
def seven_canonical_flow_cells(
    hiseq_x_single_index_flow_cell: IlluminaRunDirectoryData,
    hiseq_x_dual_index_flow_cell: IlluminaRunDirectoryData,
    hiseq_2500_dual_index_flow_cell: IlluminaRunDirectoryData,
    hiseq_2500_custom_index_flow_cell: IlluminaRunDirectoryData,
    novaseq_6000_pre_1_5_kits_flow_cell: IlluminaRunDirectoryData,
    novaseq_6000_post_1_5_kits_flow_cell: IlluminaRunDirectoryData,
    novaseq_x_flow_cell: IlluminaRunDirectoryData,
) -> list[IlluminaRunDirectoryData]:
    """Return a list with the seven canonical flow cells."""
    return [
        hiseq_x_single_index_flow_cell,
        hiseq_x_dual_index_flow_cell,
        hiseq_2500_dual_index_flow_cell,
        hiseq_2500_custom_index_flow_cell,
        novaseq_6000_pre_1_5_kits_flow_cell,
        novaseq_6000_post_1_5_kits_flow_cell,
        novaseq_x_flow_cell,
    ]


# Demultiplexed runs


@pytest.fixture
def novaseqx_flow_cell_with_sample_sheet_no_fastq(
    tmp_demultiplexed_flow_cell_no_fastq_files: Path,
) -> IlluminaRunDirectoryData:
    """Return a flow cell from a tmp dir with a sample sheet and no sample fastq files."""
    tmp_demultiplexed_flow_cell_no_fastq_files.mkdir(parents=True, exist_ok=True)
    flow_cell = IlluminaRunDirectoryData(tmp_demultiplexed_flow_cell_no_fastq_files)
    sample_sheet_path = Path(flow_cell.path, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)
    flow_cell._sample_sheet_path_hk = sample_sheet_path
    return flow_cell


@pytest.fixture
def tmp_bcl_convert_flow_cell(
    tmp_flow_cell_directory_bcl_convert: Path,
) -> IlluminaRunDirectoryData:
    """Create a flow cell object with flow cell that is demultiplexed."""
    return IlluminaRunDirectoryData(tmp_flow_cell_directory_bcl_convert)


@pytest.fixture
def hiseq_x_single_index_demultiplexed_flow_cell_with_sample_sheet(
    illumina_demultiplexed_runs_directory: Path,
    hiseq_x_single_index_flow_cell_name: str,
    hiseq_x_single_index_sample_sheet_path: Path,
) -> IlluminaRunDirectoryData:
    """Return a Novaseq6000 flow cell with a sample sheet."""
    path = Path(illumina_demultiplexed_runs_directory, hiseq_x_single_index_flow_cell_name)
    flow_cell = IlluminaRunDirectoryData(path)
    flow_cell.set_sample_sheet_path_hk(hiseq_x_single_index_sample_sheet_path)
    return flow_cell


@pytest.fixture
def novaseq_x_demux_runs_flow_cell(
    novaseq_x_demux_runs_dir: Path, novaseq_x_flow_cell: IlluminaRunDirectoryData
) -> IlluminaRunDirectoryData:
    """Return a NovaSeqX flow cell."""
    demux_run = IlluminaRunDirectoryData(novaseq_x_demux_runs_dir)
    demux_run.set_sample_sheet_path_hk(novaseq_x_flow_cell.path / "SampleSheet.csv")
    return demux_run


@pytest.fixture
def hiseq_2500_dual_index_demux_runs_flow_cell(
    hiseq_2500_dual_index_demux_runs_dir: Path,
) -> IlluminaRunDirectoryData:
    """Return a HiSeq2500 flow cell."""
    return IlluminaRunDirectoryData(hiseq_2500_dual_index_demux_runs_dir)
