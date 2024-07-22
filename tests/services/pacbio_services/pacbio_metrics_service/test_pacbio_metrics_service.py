import shutil
from pathlib import Path
from typing import Callable

import pytest
from _pytest.fixtures import FixtureRequest

from cg.constants.pacbio import PacBioDirsAndFiles
from cg.exc import PacBioMetricsParsingError
from cg.services.pacbio.metrics.models import BaseMetrics
from cg.services.pacbio.metrics.utils import (
    parse_control_metrics,
    parse_dataset_metrics,
    parse_hifi_metrics,
    parse_polymerase_metrics,
    parse_productivity_metrics,
)


@pytest.mark.parametrize(
    "parsing_function, expected_metrics_fixture",
    [
        (parse_control_metrics, "pac_bio_control_metrics"),
        (parse_dataset_metrics, "pac_bio_smrtlink_databases_metrics"),
        (parse_hifi_metrics, "pac_bio_hifi_metrics"),
        (parse_productivity_metrics, "pac_bio_productivity_metrics"),
        (parse_polymerase_metrics, "pac_bio_polymerase_metrics"),
    ],
    ids=["Control", "Smrtlink-Dataset", "Hi-Fi", "Productivity", "Polymerase"],
)
def test_parse_dataset_metrics(
    parsing_function: Callable,
    expected_metrics_fixture: str,
    pac_bio_run_statistics_dir: Path,
    request: FixtureRequest,
):
    """Test the parsing of all PacBio metric files."""
    # GIVEN a metrics file to parse in an existing statistics directory

    # WHEN parsing the SMRTlink datasets metrics
    parsed_metrics: BaseMetrics = parsing_function(report_dir=pac_bio_run_statistics_dir)

    # THEN the parsed metrics are the expected ones
    expected_metrics: BaseMetrics = request.getfixturevalue(expected_metrics_fixture)
    assert parsed_metrics == expected_metrics


@pytest.mark.parametrize(
    "parsing_function",
    [
        parse_control_metrics,
        parse_dataset_metrics,
        parse_hifi_metrics,
        parse_productivity_metrics,
        parse_polymerase_metrics,
    ],
    ids=["Control", "Smrtlink-Dataset", "Hi-Fi", "Productivity", "Polymerase"],
)
def test_parse_dataset_metrics_missing_file(tmp_path: Path, parsing_function: Callable):
    """Test the parsing of all PacBio metric files with a missing file raises an error."""
    # GIVEN a directory with no metrics files to parse

    # WHEN parsing the metrics
    with pytest.raises(PacBioMetricsParsingError) as error:
        # THEN a PacBioMetricsParsingError is raised
        parse_dataset_metrics(report_dir=tmp_path)
    assert "Could not find the metrics file" in str(error.value)
    assert tmp_path.as_posix() in str(error.value)


@pytest.mark.parametrize(
    "parsing_function, metrics_file_name",
    [
        (parse_control_metrics, PacBioDirsAndFiles.CONTROL_REPORT),
        (parse_dataset_metrics, PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT),
        (parse_hifi_metrics, PacBioDirsAndFiles.BASECALLING_REPORT),
        (parse_productivity_metrics, PacBioDirsAndFiles.LOADING_REPORT),
        (parse_polymerase_metrics, PacBioDirsAndFiles.RAW_DATA_REPORT),
    ],
    ids=["Control", "Smrtlink-Dataset", "Hi-Fi", "Productivity", "Polymerase"],
)
def test_parse_dataset_metrics_validation_error(
    tmp_path: Path,
    parsing_function: Callable,
    metrics_file_name: str,
    pac_bio_wrong_metrics_file: Path,
):
    """Test the parsing of all PacBio metric files with an unexpected error raises an error."""
    # GIVEN a tmp statistics directory with a metrics file without the expected structure
    shutil.copyfile(src=pac_bio_wrong_metrics_file, dst=Path(tmp_path, metrics_file_name))
    assert Path(tmp_path, metrics_file_name).exists()

    # WHEN parsing the metrics
    with pytest.raises(PacBioMetricsParsingError) as error:
        # THEN a PacBioMetricsParsingError is raised
        parsing_function(report_dir=tmp_path)
    assert "An error occurred while parsing the metrics" in str(error.value)
