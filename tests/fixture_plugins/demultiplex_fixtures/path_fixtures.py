"""Path fixtures for demultiplex tests."""

import shutil
from pathlib import Path

import pytest

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.nanopore_files import NanoporeDirsAndFiles
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData

CORRECT_SAMPLE_SHEET: str = "CorrectSampleSheet.csv"


@pytest.fixture
def tmp_flow_cells_directory(tmp_path: Path, flow_cells_dir: Path) -> Path:
    """
    Return the path to a temporary flow cells directory with flow cells ready for demultiplexing.
    Generates a copy of the original flow cells directory
    """
    original_dir = flow_cells_dir
    tmp_dir = Path(tmp_path, "flow_cells")

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


@pytest.fixture
def tmp_flow_cells_demux_all_directory(tmp_path: Path, flow_cells_demux_all_dir: Path) -> Path:
    """
    Return the path to a temporary flow cells directory with flow cells ready for demultiplexing.
    Generates a copy of the original flow cells directory.
    This fixture is used for testing of the cg demutliplex all cmd.
    """
    original_dir = flow_cells_demux_all_dir
    tmp_dir = Path(tmp_path, "flow_cells_demux_all")

    return Path(shutil.copytree(original_dir, tmp_dir))


@pytest.fixture(name="tmp_flow_cell_directory_bcl2fastq")
def flow_cell_working_directory_bcl2fastq(
    bcl2fastq_flow_cell_dir: Path, tmp_flow_cells_directory: Path
) -> Path:
    """Return the path to a working directory that will be deleted after test is run.

    This is a path to a flow cell directory with the run parameters present.
    """
    return Path(tmp_flow_cells_directory, bcl2fastq_flow_cell_dir.name)


@pytest.fixture(name="tmp_flow_cell_directory_bclconvert")
def flow_cell_working_directory_bclconvert(
    bcl_convert_flow_cell_dir: Path, tmp_flow_cells_directory: Path
) -> Path:
    """Return the path to a working directory that will be deleted after test is run.
    This is a path to a flow cell directory with the run parameters present.
    """
    return Path(tmp_flow_cells_directory, bcl_convert_flow_cell_dir.name)


@pytest.fixture
def tmp_flow_cell_without_run_parameters_path(
    tmp_broken_flow_cells_directory: Path, hiseq_2500_custom_index_flow_cell_name: str
) -> Path:
    """This is a path to a flow cell directory with the run parameters missing."""
    return Path(tmp_broken_flow_cells_directory, hiseq_2500_custom_index_flow_cell_name)


@pytest.fixture
def tmp_novaseq_6000_pre_1_5_kits_flow_cell_without_sample_sheet_path(
    tmp_broken_flow_cells_directory: Path,
) -> Path:
    """This is a path to a flow cell directory with the sample sheet missing."""
    return Path(tmp_broken_flow_cells_directory, "190927_A00689_0069_BHLYWYDSXX")


@pytest.fixture
def tmp_novaseq_6000_post_1_5_kits_flow_cell_without_sample_sheet_path(
    tmp_broken_flow_cells_directory: Path,
) -> Path:
    """This is a path to a flow cell directory with the sample sheet missing."""
    return Path(tmp_broken_flow_cells_directory, "230912_A00187_1009_AHK33MDRX3")


@pytest.fixture
def tmp_novaseq_x_without_sample_sheet_flow_cell_path(
    tmp_broken_flow_cells_directory: Path,
) -> Path:
    """This is a path to a flow cell directory with the sample sheet missing."""
    return Path(tmp_broken_flow_cells_directory, "20231108_LH00188_0028_B22F52TLT3")


@pytest.fixture
def tmp_flow_cells_directory_malformed_sample_sheet(
    tmp_flow_cell_name_malformed_sample_sheet: str, tmp_flow_cells_directory: Path
) -> Path:
    """This is a path to a flow cell directory with a sample sheet with malformed headers."""
    return Path(tmp_flow_cells_directory, tmp_flow_cell_name_malformed_sample_sheet)


@pytest.fixture
def tmp_flow_cells_directory_ready_for_demultiplexing_bcl_convert(
    bcl_convert_flow_cell_full_name: str, tmp_flow_cells_directory: Path
) -> Path:
    """This is a path to a flow cell directory with the run parameters missing."""
    return Path(tmp_flow_cells_directory, bcl_convert_flow_cell_full_name)


@pytest.fixture
def tmp_flow_cells_directory_ready_for_demultiplexing_bcl2fastq(
    tmp_flow_cell_name_ready_for_demultiplexing_bcl2fastq: str, tmp_flow_cells_directory: Path
) -> Path:
    """This is a path to a flow cell directory with the run parameters missing."""
    return Path(tmp_flow_cells_directory, tmp_flow_cell_name_ready_for_demultiplexing_bcl2fastq)


# Temporary demultiplexed runs fixtures
@pytest.fixture(name="tmp_demultiplexed_runs_directory")
def tmp_demultiplexed_flow_cells_directory(tmp_path: Path, demultiplexed_runs: Path) -> Path:
    """Return the path to a temporary demultiplex-runs directory.
    Generates a copy of the original demultiplexed-runs
    """
    original_dir = demultiplexed_runs
    tmp_dir = Path(tmp_path, "demultiplexed-runs")
    return Path(shutil.copytree(original_dir, tmp_dir))


@pytest.fixture(name="tmp_demultiplexed_runs_bcl2fastq_directory")
def tmp_demultiplexed_runs_bcl2fastq_directory(
    tmp_demultiplexed_runs_directory: Path, bcl2fastq_flow_cell_dir: Path
) -> Path:
    """Return the path to a temporary demultiplex-runs bcl2fastq flow cell directory."""
    return Path(tmp_demultiplexed_runs_directory, bcl2fastq_flow_cell_dir.name)


@pytest.fixture(name="tmp_demultiplexed_runs_not_finished_directory")
def tmp_demultiplexed_runs_not_finished_flow_cells_directory(
    tmp_path: Path, demux_results_not_finished_dir: Path
) -> Path:
    """
    Return a temporary demultiplex-runs-unfinished path with an unfinished flow cell directory.
    Generates a copy of the original demultiplexed-runs-unfinished directory.
    """
    original_dir = demux_results_not_finished_dir
    tmp_dir = Path(tmp_path, "demultiplexed-runs-unfinished")
    return Path(shutil.copytree(original_dir, tmp_dir))


@pytest.fixture(name="demultiplexed_runs_unfinished_bcl2fastq_flow_cell_directory")
def demultiplexed_runs_bcl2fastq_flow_cell_directory(
    tmp_demultiplexed_runs_not_finished_directory: Path,
    bcl2fastq_flow_cell_full_name: str,
) -> Path:
    """Copy the content of a demultiplexed but not finished directory to a temporary location."""
    return Path(tmp_demultiplexed_runs_not_finished_directory, bcl2fastq_flow_cell_full_name)


@pytest.fixture(name="novaseq6000_bcl_convert_sample_sheet_path")
def novaseq6000_sample_sheet_path() -> Path:
    """Return the path to a NovaSeq 6000 BCL convert sample sheet."""
    return Path(
        "tests",
        "fixtures",
        "apps",
        "sequencing_metrics_parser",
        "230622_A00621_0864_AHY7FFDRX2",
        "Unaligned",
        "Reports",
        "SampleSheet.csv",
    )


# Directory fixtures


@pytest.fixture(scope="session")
def demultiplex_fixtures(apps_dir: Path) -> Path:
    """Return the path to the demultiplex fixture directory."""
    return Path(apps_dir, "demultiplexing")


@pytest.fixture(scope="session")
def raw_lims_sample_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the raw samples fixture directory."""
    return Path(demultiplex_fixtures, "raw_lims_samples")


@pytest.fixture(scope="session")
def run_parameters_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the run parameters fixture directory."""
    return Path(demultiplex_fixtures, "run_parameters")


@pytest.fixture(scope="session")
def demultiplexed_runs(demultiplex_fixtures: Path) -> Path:
    """Return the path to the demultiplexed flow cells fixture directory."""
    return Path(demultiplex_fixtures, "demultiplexed-runs")


@pytest.fixture(scope="session")
def flow_cells_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the sequenced flow cells fixture directory."""
    return Path(demultiplex_fixtures, DemultiplexingDirsAndFiles.FLOW_CELLS_DIRECTORY_NAME)


@pytest.fixture(scope="session")
def broken_flow_cells_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the broken or incomplete flow cells fixture directory."""
    return Path(demultiplex_fixtures, "flow_cells_broken")


@pytest.fixture(scope="session")
def nanopore_flow_cells_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the sequenced flow cells fixture directory."""
    return Path(demultiplex_fixtures, NanoporeDirsAndFiles.DATA_DIRECTORY)


@pytest.fixture(scope="session")
def flow_cells_demux_all_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the sequenced flow cells fixture directory."""
    return Path(demultiplex_fixtures, "flow_cells_demux_all")


@pytest.fixture(scope="session")
def demux_results_not_finished_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to a dir with demultiplexing results where nothing has been cleaned."""
    return Path(demultiplex_fixtures, "demultiplexed-runs-unfinished")


###


@pytest.fixture
def novaseq_6000_post_1_5_kits_flow_cell_path(tmp_flow_cells_directory: Path) -> Path:
    return Path(tmp_flow_cells_directory, "230912_A00187_1009_AHK33MDRX3")


@pytest.fixture
def novaseq_6000_post_1_5_kits_correct_sample_sheet_path(
    novaseq_6000_post_1_5_kits_flow_cell_path: Path,
) -> Path:
    return Path(novaseq_6000_post_1_5_kits_flow_cell_path, CORRECT_SAMPLE_SHEET)


@pytest.fixture
def novaseq_6000_pre_1_5_kits_flow_cell_path(tmp_flow_cells_directory: Path) -> Path:
    return Path(tmp_flow_cells_directory, "190927_A00689_0069_BHLYWYDSXX")


@pytest.fixture
def novaseq_6000_pre_1_5_kits_correct_sample_sheet_path(
    novaseq_6000_pre_1_5_kits_flow_cell_path: Path,
) -> Path:
    return Path(novaseq_6000_pre_1_5_kits_flow_cell_path, CORRECT_SAMPLE_SHEET)


@pytest.fixture
def novaseq_x_flow_cell_directory(tmp_flow_cells_directory: Path) -> Path:
    return Path(tmp_flow_cells_directory, "20231108_LH00188_0028_B22F52TLT3")


@pytest.fixture
def novaseq_x_correct_sample_sheet(novaseq_x_flow_cell_directory: Path) -> Path:
    return Path(novaseq_x_flow_cell_directory, CORRECT_SAMPLE_SHEET)


@pytest.fixture
def novaseq_x_manifest_file(novaseq_x_flow_cell_dir: Path) -> Path:
    """Return the path to a NovaSeqX manifest file."""
    return Path(novaseq_x_flow_cell_dir, "Manifest.tsv")


@pytest.fixture(scope="session")
def hiseq_x_single_index_flow_cell_dir(
    flow_cells_dir: Path, hiseq_x_single_index_flow_cell_name: str
) -> Path:
    """Return the path to a HiSeqX flow cell."""
    return Path(flow_cells_dir, hiseq_x_single_index_flow_cell_name)


@pytest.fixture(scope="session")
def hiseq_x_dual_index_flow_cell_dir(
    flow_cells_dir: Path, hiseq_x_dual_index_flow_cell_name: str
) -> Path:
    """Return the path to a HiSeqX flow cell."""
    return Path(flow_cells_dir, hiseq_x_dual_index_flow_cell_name)


@pytest.fixture(scope="session")
def hiseq_2500_dual_index_flow_cell_dir(
    flow_cells_dir: Path, hiseq_2500_dual_index_flow_cell_name: str
) -> Path:
    """Return the path to a HiSeq2500 flow cell."""
    return Path(flow_cells_dir, hiseq_2500_dual_index_flow_cell_name)


@pytest.fixture(scope="session")
def hiseq_2500_custom_index_flow_cell_dir(
    flow_cells_dir: Path, hiseq_2500_custom_index_flow_cell_name: str
) -> Path:
    """Return the path to a HiSeq2500 flow cell."""
    return Path(flow_cells_dir, hiseq_2500_custom_index_flow_cell_name)


@pytest.fixture
def novaseq_x_flow_cell_dir(flow_cells_dir: Path) -> Path:
    """Return the path to a NovaSeqX flow cell."""
    return Path(flow_cells_dir, "20231108_LH00188_0028_B22F52TLT3")


@pytest.fixture(scope="session")
def bcl2fastq_flow_cell_dir(flow_cells_dir: Path, bcl2fastq_flow_cell_full_name: str) -> Path:
    """Return the path to the bcl2fastq flow cell demultiplex fixture directory."""
    return Path(flow_cells_dir, bcl2fastq_flow_cell_full_name)


@pytest.fixture(scope="session")
def bcl_convert_flow_cell_dir(flow_cells_dir: Path, bcl_convert_flow_cell_full_name: str) -> Path:
    """Return the path to the bcl_convert flow cell demultiplex fixture directory."""
    return Path(flow_cells_dir, bcl_convert_flow_cell_full_name)


@pytest.fixture(scope="session")
def novaseq_bcl2fastq_sample_sheet_path(bcl2fastq_flow_cell_dir: Path) -> Path:
    """Return the path to a NovaSeq6000 Bcl2fastq sample sheet."""
    return Path(bcl2fastq_flow_cell_dir, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)


@pytest.fixture(scope="session")
def novaseq_bcl_convert_sample_sheet_path(bcl_convert_flow_cell_dir: Path) -> Path:
    """Return the path to a NovaSeq6000 bcl_convert sample sheet."""
    return Path(bcl_convert_flow_cell_dir, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)


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


@pytest.fixture(scope="session")
def novaseq_6000_run_parameters_path(bcl2fastq_flow_cell_dir: Path) -> Path:
    """Return the path to a NovaSeq6000 run parameters file."""
    return Path(bcl2fastq_flow_cell_dir, DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE)


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


@pytest.fixture(name="lims_novaseq_samples_file")
def lims_novaseq_samples_file(raw_lims_sample_dir: Path) -> Path:
    """Return the path to a file with sample info in lims format."""
    return Path(raw_lims_sample_dir, "raw_samplesheet_novaseq.json")


@pytest.fixture
def lims_novaseq_6000_samples_file(bcl2fastq_flow_cell_dir: Path) -> Path:
    """Return the path to the file with the raw samples of HVKJCDRXX flow cell in lims format."""
    return Path(bcl2fastq_flow_cell_dir, "HVKJCDRXX_raw.json")


@pytest.fixture(name="demultiplexed_flow_cell")
def demultiplexed_flow_cell(demultiplexed_runs: Path, bcl2fastq_flow_cell_full_name: str) -> Path:
    """Return the path to a demultiplexed flow cell with bcl2fastq."""
    return Path(demultiplexed_runs, bcl2fastq_flow_cell_full_name)


@pytest.fixture(name="bcl_convert_demultiplexed_flow_cell")
def bcl_convert_demultiplexed_flow_cell(
    demultiplexed_runs: Path, bcl_convert_flow_cell_full_name: str
) -> Path:
    """Return the path to a demultiplexed flow cell with BCLConvert."""
    return Path(demultiplexed_runs, bcl_convert_flow_cell_full_name)


# Fixtures for test demultiplex flow cell
@pytest.fixture
def tmp_empty_demultiplexed_runs_directory(tmp_demultiplexed_runs_directory) -> Path:
    return Path(tmp_demultiplexed_runs_directory, "empty")


@pytest.fixture(name="novaseqx_demultiplexed_flow_cell")
def novaseqx_demultiplexed_flow_cell(demultiplexed_runs: Path, novaseq_x_flow_cell_full_name: str):
    """Return the path to a demultiplexed NovaSeqX flow cell."""
    return Path(demultiplexed_runs, novaseq_x_flow_cell_full_name)
