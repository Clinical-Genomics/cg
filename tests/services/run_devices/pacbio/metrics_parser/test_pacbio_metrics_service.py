import shutil
from pathlib import Path
from unittest.mock import Mock, create_autospec
from xml.etree.ElementTree import Element, ParseError

import pytest
from _pytest.fixtures import FixtureRequest
from pytest_mock import MockerFixture

from cg.constants.pacbio import PacBioDirsAndFiles
from cg.exc import XMLError
from cg.services.run_devices.pacbio.metrics_parser.metrics_parser import PacBioMetricsParser
from cg.services.run_devices.pacbio.metrics_parser.models import (
    BaseMetrics,
    MetadataMetrics,
    PacBioMetrics,
)
from cg.services.run_devices.pacbio.metrics_parser.utils import (
    ElementTree,
    get_parsed_metadata_file,
    get_parsed_metrics_from_file_name,
)
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.pacbio.run_file_manager.run_file_manager import PacBioRunFileManager


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


def test_get_parsed_metadata_file_success(pacbio_barcoded_metadata_file: Path):
    # GIVEN a list of metrics files
    files = [Path("file1"), pacbio_barcoded_metadata_file]

    # WHEN parsing the metadata file
    parsed_metadata: MetadataMetrics = get_parsed_metadata_file(files)

    # THEN the output is as expected
    assert parsed_metadata == MetadataMetrics(run_name="run-name", unique_id="unique-id")


def test_get_parsed_metadata_file_parsing_fails(
    pacbio_barcoded_metadata_file: Path, mocker: MockerFixture
):
    # GIVEN a list of metrics files with a valid path
    files = [Path("file1"), pacbio_barcoded_metadata_file]

    # GIVEN that parsing the metadata file raises a ParseError
    mocker.patch.object(ElementTree, "parse", side_effect=ParseError)

    # WHEN parsing the metadata file
    # THEN an error is raised
    with pytest.raises(ParseError):
        get_parsed_metadata_file(files)


def test_get_parsed_metadata_file_run_element_not_found(
    pacbio_barcoded_metadata_file: Path, mocker: MockerFixture
):
    # GIVEN a list of metrics files with a valid path
    files = [Path("file1"), pacbio_barcoded_metadata_file]

    # GIVEN that the Run element can't be found in the XML
    tree: ElementTree.ElementTree = create_autospec(ElementTree.ElementTree)
    root: Element = create_autospec(Element)
    root.find = Mock(return_value=None)
    tree.getroot = Mock(return_value=root)
    mocker.patch.object(ElementTree, "parse", return_value=tree)

    # WHEN parsing the metadata file
    # THEN an error is raised
    with pytest.raises(XMLError):
        get_parsed_metadata_file(files)


def test_get_parsed_metadata_file_run_element_without_attributes(
    pacbio_barcoded_metadata_file: Path, mocker: MockerFixture
):
    # GIVEN a list of metrics files with a valid path
    files = [Path("file1"), pacbio_barcoded_metadata_file]

    # GIVEN that the Run element can't be found in the XML
    tree: ElementTree.ElementTree = create_autospec(ElementTree.ElementTree)
    root: Element = create_autospec(Element)
    run_element: Element = create_autospec(Element)
    run_element.get = Mock(return_value=None)
    root.find = Mock(return_value=run_element)
    tree.getroot = Mock(return_value=root)
    mocker.patch.object(ElementTree, "parse", return_value=tree)

    # WHEN parsing the metadata file
    # THEN an error is raised
    with pytest.raises(XMLError):
        get_parsed_metadata_file(files)


def test_parse_metrics(
    pacbio_barcoded_report_files_to_parse: list[Path],
    pacbio_barcoded_run_data: PacBioRunData,
    pac_bio_metrics: PacBioMetrics,
):
    # GIVEN a PacBioMetricsParser and a PacBioRunData
    file_manager = create_autospec(PacBioRunFileManager)
    file_manager.get_files_to_parse = Mock(return_value=pacbio_barcoded_report_files_to_parse)
    parser = PacBioMetricsParser(file_manager=file_manager)

    # WHEN parsing the metrics
    metrics = parser.parse_metrics(pacbio_barcoded_run_data)

    # THEN the metrics should be as expected
    assert metrics == pac_bio_metrics
