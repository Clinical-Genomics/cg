"""Module for PacBio fixtures returning Path objects."""

from pathlib import Path

import pytest

from cg.constants.pacbio import PacBioDirsAndFiles
from cg.services.run_devices.pacbio.run_file_manager.models import PacBioRunValidatorFiles


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
def pacbio_barcoded_run_dir(pac_bio_runs_dir: Path, pacbio_barcoded_run_name: str) -> Path:
    """Return the path to a PacBio run directory."""
    return Path(pac_bio_runs_dir, pacbio_barcoded_run_name)


@pytest.fixture
def pac_bio_smrt_cell_dir_1_b01(pac_bio_test_run_dir: Path, pac_bio_smrt_cell_name: str) -> Path:
    """Return the path to a PacBio SMRT cell directory."""
    return Path(pac_bio_test_run_dir, pac_bio_smrt_cell_name)


@pytest.fixture
def pacbio_barcoded_smrt_cell_dir_1_c01(
    pacbio_barcoded_run_dir: Path, pacbio_barcoded_smrt_cell_name: str
) -> Path:
    """Return the path to a barcoded PacBio SMRT cell directory."""
    return Path(pacbio_barcoded_run_dir, pacbio_barcoded_smrt_cell_name)


@pytest.fixture
def pacbio_barcoded_hifi_reads_dir(pacbio_barcoded_smrt_cell_dir_1_c01: Path) -> Path:
    """Return the path to a PacBio HiFi reads directory."""
    return Path(pacbio_barcoded_smrt_cell_dir_1_c01, PacBioDirsAndFiles.HIFI_READS)


@pytest.fixture
def pac_bio_run_statistics_dir_1_b01(pac_bio_smrt_cell_dir_1_b01: Path) -> Path:
    """Return the path to the PacBio SMRT cell statistics directory."""
    return Path(pac_bio_smrt_cell_dir_1_b01, PacBioDirsAndFiles.STATISTICS_DIR)


@pytest.fixture
def pacbio_barcoded_run_statistics_dir(pacbio_barcoded_smrt_cell_dir_1_c01: Path) -> Path:
    """Return the path to the statistics directory of the PacBio barcoded SMRT cell."""
    return Path(pacbio_barcoded_smrt_cell_dir_1_c01, PacBioDirsAndFiles.STATISTICS_DIR)


@pytest.fixture
def pac_bio_run_reports_dir_1_b01(pac_bio_run_statistics_dir_1_b01: Path) -> Path:
    """Return the path to the PacBio SMRT cell unzipped_reports directory"""
    return Path(pac_bio_run_statistics_dir_1_b01, PacBioDirsAndFiles.UNZIPPED_REPORTS_DIR)


@pytest.fixture
def pacbio_barcoded_run_reports_dir(pacbio_barcoded_run_statistics_dir: Path) -> Path:
    """Return the path to the unzipped reports directory of the PacBio barcoded SMRT cell."""
    return Path(pacbio_barcoded_run_statistics_dir, PacBioDirsAndFiles.UNZIPPED_REPORTS_DIR)


@pytest.fixture
def pac_bio_run_metadata_dir_1_b01(pac_bio_smrt_cell_dir_1_b01: Path) -> Path:
    """Return the path to the PacBio SMRT cell metadata directory"""
    return Path(pac_bio_smrt_cell_dir_1_b01, PacBioDirsAndFiles.METADATA_DIR)


# File fixtures


@pytest.fixture
def pacbio_barcodes_report_file(
    pacbio_barcoded_run_reports_dir: Path,
) -> Path:
    """Return the path to the PacBio barcodes report file."""
    return Path(pacbio_barcoded_run_reports_dir, PacBioDirsAndFiles.BARCODES_REPORT)


@pytest.fixture
def pacbio_barcoded_ccs_report_file(
    pacbio_barcoded_run_statistics_dir: Path, pacbio_barcoded_1_c01_cell_full_name: str
) -> Path:
    """Return the path to the PacBio CCS report file."""
    return Path(
        pacbio_barcoded_run_statistics_dir,
        f"{pacbio_barcoded_1_c01_cell_full_name}.{PacBioDirsAndFiles.CCS_REPORT_SUFFIX}",
    )


@pytest.fixture
def pacbio_barcoded_control_report_file(pacbio_barcoded_run_reports_dir: Path) -> Path:
    """Return the path to the PacBio loading report file."""
    return Path(pacbio_barcoded_run_reports_dir, PacBioDirsAndFiles.CONTROL_REPORT)


@pytest.fixture
def pacbio_barcoded_loading_report_file(pacbio_barcoded_run_reports_dir: Path) -> Path:
    """Return the path to the PacBio loading report file."""
    return Path(pacbio_barcoded_run_reports_dir, PacBioDirsAndFiles.LOADING_REPORT)


@pytest.fixture
def pacbio_barcoded_raw_data_report_file(pacbio_barcoded_run_reports_dir: Path) -> Path:
    """Return the path to the PacBio loading report file."""
    return Path(pacbio_barcoded_run_reports_dir, PacBioDirsAndFiles.RAW_DATA_REPORT)


@pytest.fixture
def pacbio_barcoded_smrtlink_datasets_report_file(pacbio_barcoded_run_reports_dir: Path) -> Path:
    """Return the path to the PacBio loading report file."""
    return Path(pacbio_barcoded_run_reports_dir, PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT)


@pytest.fixture
def pac_bio_transferdone_file_1_b01(pac_bio_run_metadata_dir_1_b01: Path) -> Path:
    """Return the path to the PacBio SMRTLink datasets report file."""
    return Path(pac_bio_run_metadata_dir_1_b01, "m84202_240522_155607_s2.transferdone")


@pytest.fixture
def pac_bio_zipped_reports_file_1_b01(pac_bio_run_statistics_dir_1_b01: Path) -> Path:
    """Return the path to the PacBio SMRTLink datasets report file."""
    return Path(pac_bio_run_statistics_dir_1_b01, "m84202_240522_155607_s2.reports.zip")


@pytest.fixture
def pacbio_barcoded_report_files_to_parse(
    pacbio_barcodes_report_file: Path,
    pacbio_barcoded_ccs_report_file: Path,
    pacbio_barcoded_control_report_file: Path,
    pacbio_barcoded_loading_report_file: Path,
    pacbio_barcoded_raw_data_report_file: Path,
    pacbio_barcoded_smrtlink_datasets_report_file: Path,
) -> list[Path]:
    """Return the list of PacBio report files to parse."""
    return [
        pacbio_barcodes_report_file,
        pacbio_barcoded_control_report_file,
        pacbio_barcoded_loading_report_file,
        pacbio_barcoded_raw_data_report_file,
        pacbio_barcoded_smrtlink_datasets_report_file,
        pacbio_barcoded_ccs_report_file,
    ]


@pytest.fixture
def pacbio_barcoded_hifi_read_file(
    pacbio_barcoded_hifi_reads_dir: Path, pacbio_barcoded_1_c01_cell_full_name: str
) -> Path:
    """Return the Pacbio bacrcoded HiFi read file."""
    return Path(
        pacbio_barcoded_hifi_reads_dir,
        f"{pacbio_barcoded_1_c01_cell_full_name}.hifi_reads.bc2004.bam",
    )


@pytest.fixture
def pacbio_unassigned_hifi_read_file(
    pacbio_barcoded_hifi_reads_dir: Path, pacbio_barcoded_1_c01_cell_full_name: str
) -> Path:
    """Return the Pacbio unassigned HiFi read file."""
    return Path(
        pacbio_barcoded_hifi_reads_dir,
        f"{pacbio_barcoded_1_c01_cell_full_name}.hifi_reads.unassigned.bam",
    )


@pytest.fixture
def pacbio_barcoded_hifi_read_files(pacbio_barcoded_hifi_read_file: Path) -> list[Path]:
    """Return the list of PacBio HiFi read files."""
    return [pacbio_barcoded_hifi_read_file]


@pytest.fixture
def expected_1_b01_run_validation_files(
    pac_bio_transferdone_file_1_b01: Path,
    pac_bio_zipped_reports_file_1_b01: Path,
    pac_bio_run_reports_dir_1_b01: Path,
) -> PacBioRunValidatorFiles:
    """Return the expected run validation files for the 1_B01 SMRT cell."""
    return PacBioRunValidatorFiles(
        manifest_file=pac_bio_transferdone_file_1_b01,
        decompression_target=pac_bio_zipped_reports_file_1_b01,
        decompression_destination=pac_bio_run_reports_dir_1_b01,
    )


# Wrong files


@pytest.fixture
def pac_bio_wrong_metrics_file(pac_bio_wrong_metrics_dir: Path) -> Path:
    """Return the path to a temporary PacBio statistics directory."""
    return Path(pac_bio_wrong_metrics_dir, "metrics.json")
