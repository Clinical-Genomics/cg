"""Module for demultiplex fixtures returning Path objects."""

import shutil
from pathlib import Path

import pytest

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.nanopore_files import NanoporeDirsAndFiles

CORRECT_SAMPLE_SHEET: str = "CorrectSampleSheet.csv"


# Directory fixtures


@pytest.fixture(scope="session")
def demultiplex_fixtures(apps_dir: Path) -> Path:
    """Return the path to the demultiplex fixture directory."""
    return Path(apps_dir, "demultiplexing")


@pytest.fixture(scope="session")
def illumina_sequencing_runs_directory(demultiplex_fixtures: Path) -> Path:
    """Return the path to the sequenced flow cells fixture directory."""
    return Path(demultiplex_fixtures, DemultiplexingDirsAndFiles.SEQUENCING_RUNS_DIRECTORY_NAME)


@pytest.fixture(scope="session")
def illumina_demultiplexed_runs_directory(demultiplex_fixtures: Path) -> Path:
    """Return the path to the demultiplexed flow cells fixture directory."""
    return Path(demultiplex_fixtures, "demultiplexed-runs")


@pytest.fixture(scope="session")
def illumina_demux_all_directory(demultiplex_fixtures: Path) -> Path:
    """Return the path to the sequenced flow cells fixture directory."""
    return Path(demultiplex_fixtures, "sequencing_runs_demux_all")


@pytest.fixture(scope="session")
def nanopore_flow_cells_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the sequenced flow cells fixture directory."""
    return Path(demultiplex_fixtures, NanoporeDirsAndFiles.DATA_DIRECTORY)


@pytest.fixture(scope="session")
def run_parameters_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the run parameters fixture directory."""
    return Path(demultiplex_fixtures, "run_parameters")


@pytest.fixture(scope="session")
def sample_sheet_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the sample sheet fixture directory."""
    return Path(demultiplex_fixtures, "sample_sheets")


@pytest.fixture
def fastq_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the fastq files dir."""
    return Path(demultiplex_fixtures, "fastq")


@pytest.fixture
def spring_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the fastq files dir."""
    return Path(demultiplex_fixtures, "spring")


@pytest.fixture(scope="session")
def broken_flow_cells_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the broken or incomplete flow cells fixture directory."""
    return Path(demultiplex_fixtures, "sequencing_runs_broken")


@pytest.fixture(scope="session")
def illumina_demux_results_not_finished_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to a dir with demultiplexing results where nothing has been cleaned."""
    return Path(demultiplex_fixtures, "demultiplexed-runs-unfinished")


# Temporary directory fixtures


@pytest.fixture
def tmp_illumina_sequencing_runs_directory(
    tmp_path: Path, illumina_sequencing_runs_directory: Path
) -> Path:
    """
    Return the path to a temporary flow cells directory with flow cells ready for demultiplexing.
    Generates a copy of the original flow cells directory
    """
    original_dir = illumina_sequencing_runs_directory
    tmp_dir = Path(tmp_path, "sequencing-runs")

    return Path(shutil.copytree(original_dir, tmp_dir))


@pytest.fixture
def tmp_demultiplexed_runs_flow_cell_directory(tmp_path: Path) -> Path:
    """Return the path to a demultiplexed flow cell run directory."""
    demultiplexed_runs = Path(tmp_path, "demultiplexed-runs")
    demultiplexed_runs.mkdir()
    return demultiplexed_runs


@pytest.fixture
def tmp_illumina_demultiplexed_flow_cells_directory(
    tmp_path: Path, illumina_demultiplexed_runs_directory
) -> Path:
    """Return the path to a temporary demultiplex-runs directory.
    Generates a copy of the original demultiplexed-runs
    """
    original_dir = illumina_demultiplexed_runs_directory
    tmp_dir = Path(tmp_path, "demultiplexed-runs")
    return Path(shutil.copytree(original_dir, tmp_dir))


@pytest.fixture
def tmp_illumina_flow_cells_demux_all_directory(
    tmp_path: Path, illumina_demux_all_directory: Path
) -> Path:
    """
    Return the path to a temporary flow cells directory with flow cells ready for demultiplexing.
    Generates a copy of the original flow cells directory.
    This fixture is used for testing of the cg demutliplex all cmd.
    """
    original_dir = illumina_demux_all_directory
    tmp_dir = Path(tmp_path, "sequencing_runs_demux_all")

    return Path(shutil.copytree(original_dir, tmp_dir))


@pytest.fixture
def tmp_broken_flow_cells_directory(tmp_path: Path, broken_flow_cells_dir: Path) -> Path:
    """
    Return the path to a temporary flow cells directory with incomplete or broken flow cells.
    Generates a copy of the original flow cells directory
    """
    original_dir = broken_flow_cells_dir
    tmp_dir = Path(tmp_path, "broken_flow_cells")

    return Path(shutil.copytree(original_dir, tmp_dir))


# Canonical flow cell paths


@pytest.fixture(scope="session")
def hiseq_x_single_index_flow_cell_dir(
    illumina_sequencing_runs_directory, hiseq_x_single_index_flow_cell_name: str
) -> Path:
    """Return the path to a HiSeqX flow cell."""
    return Path(illumina_sequencing_runs_directory, hiseq_x_single_index_flow_cell_name)


@pytest.fixture(scope="session")
def hiseq_x_dual_index_flow_cell_dir(
    illumina_sequencing_runs_directory, hiseq_x_dual_index_flow_cell_name: str
) -> Path:
    """Return the path to a dual-index HiSeqX flow cell."""
    return Path(illumina_sequencing_runs_directory, hiseq_x_dual_index_flow_cell_name)


@pytest.fixture(scope="session")
def hiseq_2500_dual_index_flow_cell_dir(
    illumina_sequencing_runs_directory, hiseq_2500_dual_index_flow_cell_name: str
) -> Path:
    """Return the path to a HiSeq2500 flow cell."""
    return Path(illumina_sequencing_runs_directory, hiseq_2500_dual_index_flow_cell_name)


@pytest.fixture(scope="session")
def hiseq_2500_custom_index_flow_cell_dir(
    illumina_sequencing_runs_directory, hiseq_2500_custom_index_flow_cell_name: str
) -> Path:
    """Return the path to a HiSeq2500 flow cell."""
    return Path(illumina_sequencing_runs_directory, hiseq_2500_custom_index_flow_cell_name)


@pytest.fixture
def novaseq_6000_pre_1_5_kits_flow_cell_path(
    tmp_illumina_sequencing_runs_directory: Path, novaseq_6000_pre_1_5_kits_flow_cell_full_name: str
) -> Path:
    return Path(
        tmp_illumina_sequencing_runs_directory, novaseq_6000_pre_1_5_kits_flow_cell_full_name
    )


@pytest.fixture
def novaseq_6000_post_1_5_kits_flow_cell_path(
    tmp_illumina_sequencing_runs_directory: Path,
    novaseq_6000_post_1_5_kits_flow_cell_full_name: str,
) -> Path:
    return Path(
        tmp_illumina_sequencing_runs_directory, novaseq_6000_post_1_5_kits_flow_cell_full_name
    )


@pytest.fixture
def novaseq_x_flow_cell_dir(
    illumina_sequencing_runs_directory: Path, novaseq_x_flow_cell_full_name: str
) -> Path:
    """Return the path to a NovaSeqX flow cell."""
    return Path(illumina_sequencing_runs_directory, novaseq_x_flow_cell_full_name)


# Tmp flow cell paths


@pytest.fixture
def tmp_novaseq_6000_pre_1_5_kits_flow_cell_path(
    tmp_illumina_sequencing_runs_directory: Path, novaseq_6000_pre_1_5_kits_flow_cell_full_name: str
) -> Path:
    return Path(
        tmp_illumina_sequencing_runs_directory, novaseq_6000_pre_1_5_kits_flow_cell_full_name
    )


@pytest.fixture
def tmp_illumina_flow_cells_demux_results_not_finished_directory(
    tmp_path: Path, illumina_demux_results_not_finished_dir: Path
) -> Path:
    """Return the path to a temporary flow cells directory with unfinished demultiplexing results."""
    original_dir: Path = illumina_demux_results_not_finished_dir
    tmp_dir = Path(tmp_path, "demultiplexed-runs-unfinished")

    return Path(shutil.copytree(original_dir, tmp_dir))


@pytest.fixture
def tmp_flow_cell_directory_bcl_convert(tmp_illumina_sequencing_runs_directory: Path) -> Path:
    """Return a path to a flow cell directory with the run parameters present."""
    return Path(tmp_illumina_sequencing_runs_directory, "211101_A00187_0615_AHLG5GDRZZ")


@pytest.fixture
def tmp_flow_cell_with_bcl2fastq_sample_sheet(
    tmp_broken_flow_cells_directory: Path, hiseq_x_single_index_flow_cell_name: str
) -> Path:
    """Return a path to a flow cell directory with a BCL2FASTQ sample sheet for translation."""
    return Path(tmp_broken_flow_cells_directory, hiseq_x_single_index_flow_cell_name)


@pytest.fixture
def tmp_flow_cell_without_run_parameters_path(
    tmp_broken_flow_cells_directory: Path, hiseq_2500_custom_index_flow_cell_name: str
) -> Path:
    """Return a path to a flow cell directory with the run parameters missing."""
    return Path(tmp_broken_flow_cells_directory, hiseq_2500_custom_index_flow_cell_name)


@pytest.fixture
def tmp_novaseq_6000_pre_1_5_kits_flow_cell_without_sample_sheet_path(
    tmp_broken_flow_cells_directory: Path,
    novaseq_6000_pre_1_5_kits_flow_cell_full_name: str,
) -> Path:
    """Return a path to a flow cell directory with the sample sheet missing."""
    return Path(tmp_broken_flow_cells_directory, novaseq_6000_pre_1_5_kits_flow_cell_full_name)


@pytest.fixture
def tmp_novaseq_6000_post_1_5_kits_flow_cell_without_sample_sheet_path(
    tmp_broken_flow_cells_directory: Path,
    novaseq_6000_post_1_5_kits_flow_cell_full_name: str,
) -> Path:
    """Return a path to a flow cell directory with the sample sheet missing."""
    return Path(tmp_broken_flow_cells_directory, novaseq_6000_post_1_5_kits_flow_cell_full_name)


@pytest.fixture
def tmp_novaseq_x_without_sample_sheet_flow_cell_path(
    tmp_broken_flow_cells_directory: Path,
    novaseq_x_flow_cell_full_name: str,
) -> Path:
    """Return a path to a flow cell directory with the sample sheet missing."""
    return Path(tmp_broken_flow_cells_directory, novaseq_x_flow_cell_full_name)


@pytest.fixture
def tmp_novaseqx_flow_cell_directory(tmp_path: Path, novaseq_x_flow_cell_full_name: str) -> Path:
    """Return the path to a NovaseqX flow cell directory."""
    return Path(tmp_path, novaseq_x_flow_cell_full_name)


@pytest.fixture
def tmp_flow_cells_directory_ready_for_demultiplexing(
    hiseq_2500_dual_index_flow_cell_name: str, tmp_illumina_sequencing_runs_directory
) -> Path:
    """Return a path to a flow cell directory with the run parameters missing."""
    return Path(tmp_illumina_sequencing_runs_directory, hiseq_2500_dual_index_flow_cell_name)


# Temporary demultiplexed runs fixtures


@pytest.fixture
def tmp_demultiplexed_flow_cell_no_fastq_files(
    tmp_illumina_flow_cells_demux_results_not_finished_directory: Path,
    novaseq_6000_post_1_5_kits_flow_cell_full_name: str,
) -> Path:
    """Return the path to a demultiplexed flow cell directory without fastq files."""
    return Path(
        tmp_illumina_flow_cells_demux_results_not_finished_directory,
        novaseq_6000_post_1_5_kits_flow_cell_full_name,
    )


@pytest.fixture
def tmp_demultiplexed_novaseq_6000_post_1_5_kits_path(
    tmp_illumina_demultiplexed_flow_cells_directory: Path,
    novaseq_6000_post_1_5_kits_flow_cell_full_name: str,
) -> Path:
    """Return the path to a demultiplexed flow cell directory without fastq files."""
    return Path(
        tmp_illumina_demultiplexed_flow_cells_directory,
        novaseq_6000_post_1_5_kits_flow_cell_full_name,
    )


# Fixtures for test demultiplex flow cell
@pytest.fixture
def tmp_empty_demultiplexed_runs_directory(
    tmp_illumina_demultiplexed_flow_cells_directory,
) -> Path:
    return Path(tmp_illumina_demultiplexed_flow_cells_directory, "empty")


@pytest.fixture(scope="function")
def novaseqx_latest_analysis_version() -> str:
    """Return the latest analysis version for NovaseqX analysis data directory."""
    return "2"


def add_novaseqx_analysis_data(novaseqx_flow_cell_directory: Path, analysis_version: str):
    """Add NovaSeqX analysis data to a flow cell directory."""
    analysis_path: Path = Path(
        novaseqx_flow_cell_directory, DemultiplexingDirsAndFiles.ANALYSIS, analysis_version
    )
    analysis_path.mkdir(parents=True)
    analysis_path.joinpath(DemultiplexingDirsAndFiles.COPY_COMPLETE).touch()
    data = analysis_path.joinpath(DemultiplexingDirsAndFiles.DATA)
    data.mkdir()
    data.joinpath(DemultiplexingDirsAndFiles.ANALYSIS_COMPLETED).touch()


@pytest.fixture(scope="function")
def novaseqx_flow_cell_dir_with_analysis_data(
    tmp_novaseqx_flow_cell_directory: Path, novaseqx_latest_analysis_version: str
) -> Path:
    """Return the path to a NovaseqX flow cell directory with multiple analysis data directories."""
    add_novaseqx_analysis_data(tmp_novaseqx_flow_cell_directory, "0")
    add_novaseqx_analysis_data(tmp_novaseqx_flow_cell_directory, "1")
    add_novaseqx_analysis_data(tmp_novaseqx_flow_cell_directory, novaseqx_latest_analysis_version)
    return tmp_novaseqx_flow_cell_directory


@pytest.fixture(scope="function")
def post_processed_novaseqx_flow_cell(novaseqx_flow_cell_dir_with_analysis_data: Path) -> Path:
    """Return the path to a NovaseqX flow cell that is post processed."""
    Path(
        novaseqx_flow_cell_dir_with_analysis_data,
        DemultiplexingDirsAndFiles.QUEUED_FOR_POST_PROCESSING,
    ).touch()
    return novaseqx_flow_cell_dir_with_analysis_data


@pytest.fixture(scope="function")
def novaseqx_flow_cell_analysis_incomplete(
    tmp_novaseqx_flow_cell_directory: Path, novaseqx_latest_analysis_version: str
) -> Path:
    """
    Return the path to a flow cell for which the analysis is not complete.
    It misses the ANALYSIS_COMPLETED file.
    """
    Path(
        tmp_novaseqx_flow_cell_directory,
        DemultiplexingDirsAndFiles.ANALYSIS,
        novaseqx_latest_analysis_version,
    ).mkdir(parents=True)
    Path(
        tmp_novaseqx_flow_cell_directory,
        DemultiplexingDirsAndFiles.ANALYSIS,
        novaseqx_latest_analysis_version,
        DemultiplexingDirsAndFiles.COPY_COMPLETE,
    ).touch()
    return tmp_novaseqx_flow_cell_directory


@pytest.fixture(scope="function")
def demultiplex_not_complete_novaseqx_flow_cell(tmp_file: Path) -> Path:
    """Return the path to a NovaseqX flow cell for which demultiplexing is not complete."""
    return tmp_file


@pytest.fixture
def novaseq_x_demux_runs_dir(
    illumina_demultiplexed_runs_directory: Path, novaseq_x_flow_cell_full_name: str
) -> Path:
    """Return the path to a NovaSeqX flow cell."""
    return Path(illumina_demultiplexed_runs_directory, novaseq_x_flow_cell_full_name)


@pytest.fixture
def hiseq_2500_dual_index_demux_runs_dir(
    illumina_sequencing_runs_directory, hiseq_2500_dual_index_flow_cell_name: str
) -> Path:
    """Return the path to a HiSeq2500 flow cell."""
    return Path(illumina_sequencing_runs_directory, hiseq_2500_dual_index_flow_cell_name)


# Path to run parameter files


@pytest.fixture(scope="session")
def run_parameters_wrong_instrument(run_parameters_dir: Path) -> Path:
    """Return a NovaSeqX run parameters file path with a wrong instrument value."""
    return Path(run_parameters_dir, "RunParameters_novaseq_X_wrong_instrument.xml")


@pytest.fixture(scope="session")
def hiseq_x_single_index_run_parameters_path(
    hiseq_x_single_index_flow_cell_dir: Path,
) -> Path:
    """Return the path to a HiSeqX run parameters file with single index."""
    return Path(
        hiseq_x_single_index_flow_cell_dir, DemultiplexingDirsAndFiles.RUN_PARAMETERS_CAMEL_CASE
    )


@pytest.fixture(scope="session")
def hiseq_x_dual_index_run_parameters_path(
    hiseq_x_dual_index_flow_cell_dir: Path,
) -> Path:
    """Return the path to a HiSeqX run parameters file with dual index."""
    return Path(
        hiseq_x_dual_index_flow_cell_dir, DemultiplexingDirsAndFiles.RUN_PARAMETERS_CAMEL_CASE
    )


@pytest.fixture(scope="session")
def hiseq_2500_dual_index_run_parameters_path(
    hiseq_2500_dual_index_flow_cell_dir: Path,
) -> Path:
    """Return the path to a HiSeq2500 run parameters file with dual index."""
    return Path(
        hiseq_2500_dual_index_flow_cell_dir, DemultiplexingDirsAndFiles.RUN_PARAMETERS_CAMEL_CASE
    )


@pytest.fixture(scope="session")
def hiseq_2500_custom_index_run_parameters_path(
    hiseq_2500_custom_index_flow_cell_dir: Path,
) -> Path:
    """Return the path to a HiSeq2500 run parameters file with custom index."""
    return Path(
        hiseq_2500_custom_index_flow_cell_dir, DemultiplexingDirsAndFiles.RUN_PARAMETERS_CAMEL_CASE
    )


@pytest.fixture
def novaseq_6000_run_parameters_path(novaseq_6000_pre_1_5_kits_flow_cell_path: Path) -> Path:
    """Return the path to a NovaSeq6000 run parameters file."""
    return Path(
        novaseq_6000_pre_1_5_kits_flow_cell_path,
        DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE,
    )


@pytest.fixture
def novaseq_6000_run_parameters_pre_1_5_kits_path(
    novaseq_6000_pre_1_5_kits_flow_cell_path: Path,
) -> Path:
    """Return the path to a NovaSeq6000 pre 1.5 kit run parameters file."""
    return Path(
        novaseq_6000_pre_1_5_kits_flow_cell_path,
        DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE,
    )


@pytest.fixture
def novaseq_6000_run_parameters_post_1_5_kits_path(
    novaseq_6000_post_1_5_kits_flow_cell_path: Path,
) -> Path:
    """Return the path to a NovaSeq6000 post 1.5 kit run parameters file."""
    return Path(
        novaseq_6000_post_1_5_kits_flow_cell_path,
        DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE,
    )


@pytest.fixture
def novaseq_x_run_parameters_path(novaseq_x_flow_cell_dir: Path) -> Path:
    """Return the path to a NovaSeqX run parameters file."""
    return Path(novaseq_x_flow_cell_dir, DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE)


@pytest.fixture(scope="module")
def run_parameters_missing_versions_path(
    run_parameters_dir: Path,
) -> Path:
    """Return a NovaSeq6000 run parameters path without software and reagent kit versions."""
    return Path(run_parameters_dir, "RunParameters_novaseq_no_software_nor_reagent_version.xml")


# Path to sample sheets


@pytest.fixture
def hiseq_x_single_index_sample_sheet_path(hiseq_x_single_index_flow_cell_dir: Path) -> Path:
    """Return the path to a single-index HiSeqX sample sheet."""
    return Path(
        hiseq_x_single_index_flow_cell_dir, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
    )


@pytest.fixture
def hiseq_x_dual_index_sample_sheet_path(hiseq_x_dual_index_flow_cell_dir: Path) -> Path:
    """Return the path to a dual-index HiSeqX sample sheet."""
    return Path(hiseq_x_dual_index_flow_cell_dir, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)


@pytest.fixture
def hiseq_2500_dual_index_sample_sheet_path(hiseq_2500_dual_index_flow_cell_dir: Path) -> Path:
    """Return the path to a dual-index HiSeq2500 sample sheet."""
    return Path(
        hiseq_2500_dual_index_flow_cell_dir, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
    )


@pytest.fixture
def hiseq_2500_custom_index_sample_sheet_path(hiseq_2500_custom_index_flow_cell_dir: Path) -> Path:
    """Return the path to a custom-index HiSeq2500 sample sheet."""
    return Path(
        hiseq_2500_custom_index_flow_cell_dir, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
    )


@pytest.fixture
def novaseq_6000_pre_1_5_kits_correct_sample_sheet_path(
    novaseq_6000_pre_1_5_kits_flow_cell_path: Path,
) -> Path:
    return Path(novaseq_6000_pre_1_5_kits_flow_cell_path, CORRECT_SAMPLE_SHEET)


@pytest.fixture
def novaseq_6000_post_1_5_kits_correct_sample_sheet_path(
    novaseq_6000_post_1_5_kits_flow_cell_path: Path,
) -> Path:
    return Path(novaseq_6000_post_1_5_kits_flow_cell_path, CORRECT_SAMPLE_SHEET)


@pytest.fixture
def novaseq_x_correct_sample_sheet(novaseq_x_flow_cell_dir: Path) -> Path:
    return Path(novaseq_x_flow_cell_dir, CORRECT_SAMPLE_SHEET)


@pytest.fixture
def novaseq_6000_sample_sheet_with_reversed_cycles(sample_sheet_dir: Path) -> Path:
    """Return the path to a NovaSeq6000 sample sheet with reversed index2 cycles."""
    return Path(sample_sheet_dir, "novaseq_6000_sample_sheet_with_reversed_cycles.csv")


@pytest.fixture
def novaseq_x_sample_sheet_with_forward_cycles(sample_sheet_dir: Path) -> Path:
    """Return the path to a NovaSeqX sample sheet with forward index2 cycles."""
    return Path(sample_sheet_dir, "novaseq_x_sample_sheet_with_forward_cycles.csv")


# Path to other flow cell attributes


@pytest.fixture
def novaseq_x_manifest_file(novaseq_x_flow_cell_dir: Path) -> Path:
    """Return the path to a NovaSeqX manifest file."""
    return Path(novaseq_x_flow_cell_dir, "Manifest.tsv")


@pytest.fixture(name="fastq_file")
def fastq_file(fastq_dir: Path) -> Path:
    """Return the path to a FASTQ file."""
    return Path(fastq_dir, "dummy_run_R1_001.fastq.gz")


@pytest.fixture(name="fastq_file_father")
def fastq_file_father(fastq_dir: Path) -> Path:
    """Return the path to a FASTQ file."""
    return Path(fastq_dir, "fastq_run_R1_001.fastq.gz")


@pytest.fixture(name="spring_file")
def spring_file(spring_dir: Path) -> Path:
    """Return the path to an existing spring file."""
    return Path(spring_dir, "dummy_run_001.spring")


@pytest.fixture(name="spring_meta_data_file")
def spring_meta_data_file(spring_dir: Path) -> Path:
    """Return the path to an existing spring file."""
    return Path(spring_dir, "dummy_spring_meta_data.json")


@pytest.fixture(name="spring_file_father")
def spring_file_father(spring_dir: Path) -> Path:
    """Return the path to a second existing spring file."""
    return Path(spring_dir, "dummy_run_002.spring")
