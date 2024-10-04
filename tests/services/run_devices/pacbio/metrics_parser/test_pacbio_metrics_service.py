import shutil
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest

from cg.constants.pacbio import PacBioDirsAndFiles
from cg.services.run_devices.pacbio.metrics_parser.models import BaseMetrics
from cg.services.run_devices.pacbio.metrics_parser.utils import get_parsed_metrics_from_file_name


@pytest.mark.parametrize(
    "file_name, expected_metrics_fixture",
    [
        (PacBioDirsAndFiles.CONTROL_REPORT, "pac_bio_control_metrics"),
        (PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT, "pac_bio_smrtlink_databases_metrics"),
        (PacBioDirsAndFiles.CCS_REPORT_SUFFIX, "pac_bio_read_metrics"),
        (PacBioDirsAndFiles.LOADING_REPORT, "pac_bio_productivity_metrics"),
        (PacBioDirsAndFiles.RAW_DATA_REPORT, "pac_bio_polymerase_metrics"),
    ],
    ids=["Control", "Smrtlink-Dataset", "Read", "Productivity", "Polymerase"],
)
def test_get_parsed_metrics_from_file_name(
    file_name: str,
    expected_metrics_fixture: str,
    pacbio_barcoded_report_files_to_parse: list[Path],
    request: FixtureRequest,
):
    """Test the parsing of all PacBio metric files."""
    # GIVEN a correct list of metrics files to parse

    # WHEN parsing the SMRTlink datasets metrics
    parsed_metrics: BaseMetrics = get_parsed_metrics_from_file_name(
        metrics_files=pacbio_barcoded_report_files_to_parse, file_name=file_name
    )

    # THEN the parsed metrics are the expected ones
    expected_metrics: BaseMetrics = request.getfixturevalue(expected_metrics_fixture)
    assert parsed_metrics == expected_metrics


@pytest.mark.parametrize(
    "file_name",
    [
        PacBioDirsAndFiles.CONTROL_REPORT,
        PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT,
        PacBioDirsAndFiles.CCS_REPORT_SUFFIX,
        PacBioDirsAndFiles.LOADING_REPORT,
        PacBioDirsAndFiles.RAW_DATA_REPORT,
    ],
    ids=["Control", "Smrtlink-Dataset", "Read", "Productivity", "Polymerase"],
)
def test_get_parsed_metrics_from_missing_file(tmp_path: Path, file_name: str):
    """Test that providing a list of non-existing files to the parser raises an error."""
    # GIVEN a list of non-existing paths
    metrics_files: list[Path] = [Path(tmp_path, "non_existing_file.json")]

    # WHEN parsing the metrics
    with pytest.raises(FileNotFoundError):
        # THEN a PacBioMetricsParsingError is raised
        get_parsed_metrics_from_file_name(metrics_files=metrics_files, file_name=file_name)


@pytest.mark.parametrize(
    "metrics_file_name",
    [
        PacBioDirsAndFiles.CONTROL_REPORT,
        PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT,
        PacBioDirsAndFiles.CCS_REPORT_SUFFIX,
        PacBioDirsAndFiles.LOADING_REPORT,
        PacBioDirsAndFiles.RAW_DATA_REPORT,
    ],
    ids=["Control", "Smrtlink-Dataset", "Read", "Productivity", "Polymerase"],
)
def test_parse_dataset_metrics_validation_error(
    tmp_path: Path,
    metrics_file_name: str,
    pac_bio_wrong_metrics_file: Path,
):
    """Test the parsing of all PacBio metric files with an unexpected error raises an error."""
    # GIVEN a tmp statistics directory with a metrics file without the expected structure
    new_path = Path(tmp_path, metrics_file_name)
    shutil.copyfile(src=pac_bio_wrong_metrics_file, dst=new_path)
    assert new_path.exists()
    metrics_files: list[Path] = [new_path]

    # WHEN parsing the metrics
    with pytest.raises(Exception):
        # THEN a PacBioMetricsParsingError is raised
        get_parsed_metrics_from_file_name(metrics_files=metrics_files, file_name=metrics_file_name)
