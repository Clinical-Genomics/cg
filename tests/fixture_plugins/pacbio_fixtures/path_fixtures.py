"""Module for PacBio fixtures returning Path objects."""

from pathlib import Path

import pytest

from cg.constants.pacbio import PacBioDirsAndFiles


# Directory fixtures
@pytest.fixture
def pac_bio_fixtures_dir(devices_dir: Path) -> Path:
    """Return the path to the PacBio fixtures directory."""
    return Path(devices_dir, "pacbio")


@pytest.fixture
def pac_bio_wrong_metrics_dir(pac_bio_fixtures_dir: Path) -> Path:
    """Return the path to the PacBio metrics directory."""
    return Path(pac_bio_fixtures_dir, "wrong_metrics")


@pytest.fixture
def pac_bio_runs_dir(pac_bio_fixtures_dir: Path) -> Path:
    """Return the path to the PacBio run directory."""
    return Path(pac_bio_fixtures_dir, "SMRTcells")


@pytest.fixture
def pac_bio_test_run_dir(pac_bio_runs_dir: Path, pac_bio_test_run_name: str) -> Path:
    """Return the path to a PacBio run directory."""
    return Path(pac_bio_runs_dir, pac_bio_test_run_name)


@pytest.fixture
def pac_bio_smrt_cell_dir_1_a01(pac_bio_test_run_dir: Path, pac_bio_smrt_cell_name: str) -> Path:
    """Return the path to a PacBio SMRT cell directory."""
    return Path(pac_bio_test_run_dir, pac_bio_smrt_cell_name)


@pytest.fixture
def pac_bio_hifi_reads_dir(pac_bio_smrt_cell_dir_1_a01: Path) -> Path:
    """Return the path to a PacBio HiFi reads directory."""
    return Path(pac_bio_smrt_cell_dir_1_a01, PacBioDirsAndFiles.HIFI_READS)


@pytest.fixture
def pac_bio_run_statistics_dir(pac_bio_smrt_cell_dir_1_a01: Path) -> Path:
    """Return the path to the PacBio SMRT cell statistics directory."""
    return Path(pac_bio_smrt_cell_dir_1_a01, PacBioDirsAndFiles.STATISTICS_DIR)


@pytest.fixture
def pac_bio_run_reports_dir(pac_bio_run_statistics_dir: Path) -> Path:
    """Return the path to the PacBio SMRT cell unzipped_reports directory"""
    return Path(pac_bio_run_statistics_dir, PacBioDirsAndFiles.UNZIPPED_REPORTS_DIR)


@pytest.fixture
def pac_bio_wrong_metrics_file(pac_bio_wrong_metrics_dir: Path) -> Path:
    """Return the path to a temporary PacBio statistics directory."""
    return Path(pac_bio_wrong_metrics_dir, "metrics.json")


# File fixtures


@pytest.fixture
def pac_bio_ccs_report_file(
    pac_bio_run_statistics_dir: Path, pac_bio_1_a01_cell_full_name: str
) -> Path:
    """Return the path to the PacBio CCS report file."""
    return Path(
        pac_bio_run_statistics_dir,
        f"{pac_bio_1_a01_cell_full_name}.{PacBioDirsAndFiles.CCS_REPORT_SUFFIX}",
    )


@pytest.fixture
def pac_bio_control_report_file(pac_bio_run_reports_dir: Path) -> Path:
    """Return the path to the PacBio control report file."""
    return Path(pac_bio_run_reports_dir, PacBioDirsAndFiles.CONTROL_REPORT)


@pytest.fixture
def pac_bio_loading_report_file(pac_bio_run_reports_dir: Path) -> Path:
    """Return the path to the PacBio loading report file."""
    return Path(pac_bio_run_reports_dir, PacBioDirsAndFiles.LOADING_REPORT)


@pytest.fixture
def pac_bio_raw_data_report_file(pac_bio_run_reports_dir: Path) -> Path:
    """Return the path to the PacBio raw data report file."""
    return Path(pac_bio_run_reports_dir, PacBioDirsAndFiles.RAW_DATA_REPORT)


@pytest.fixture
def pac_bio_smrtlink_datasets_report_file(pac_bio_run_reports_dir: Path) -> Path:
    """Return the path to the PacBio SMRTLink datasets report file."""
    return Path(pac_bio_run_reports_dir, PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT)


@pytest.fixture
def pac_bio_report_files_to_parse(
    pac_bio_ccs_report_file: Path,
    pac_bio_control_report_file: Path,
    pac_bio_loading_report_file: Path,
    pac_bio_raw_data_report_file: Path,
    pac_bio_smrtlink_datasets_report_file: Path,
) -> list[Path]:
    """Return the list of PacBio report files to parse."""
    return [
        pac_bio_control_report_file,
        pac_bio_loading_report_file,
        pac_bio_raw_data_report_file,
        pac_bio_smrtlink_datasets_report_file,
        pac_bio_ccs_report_file,
    ]


@pytest.fixture
def pac_bio_hifi_read_file(pac_bio_hifi_reads_dir: Path, pac_bio_1_a01_cell_full_name: str) -> Path:
    """Return the PacBio HiFi read file."""
    return Path(pac_bio_hifi_reads_dir, f"{pac_bio_1_a01_cell_full_name}.hifi_reads.bam")
