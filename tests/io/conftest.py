from collections import namedtuple
from pathlib import Path

import pytest

FileRepresentation = namedtuple("FileRepresentation", "filepath content output_file")


@pytest.fixture
def delimiter_map(
    csv_file_path, csv_stream, csv_temp_path, tsv_file_path, tsv_stream, tsv_temp_path
):
    """Returns a dict where each entry links a delimeter linked to named tuple containing
    relevant fixtures for that delimter."""
    return {
        ",": FileRepresentation(csv_file_path, csv_stream, csv_temp_path),
        "\t": FileRepresentation(tsv_file_path, tsv_stream, tsv_temp_path),
    }


@pytest.fixture
def json_stream() -> str:
    """Return string with json format"""
    _content = """{"Lorem": {"ipsum": "sit"}}"""
    return _content


@pytest.fixture
def json_file_path(fixtures_dir: Path) -> Path:
    """Return a file path to example json file"""
    return Path(fixtures_dir, "io", "example_json.json")


@pytest.fixture
def json_temp_path(cg_dir: Path) -> Path:
    """Return a temp file path to use when writing json"""
    return Path(cg_dir, "write_json.json")


@pytest.fixture
def yaml_stream() -> str:
    """Return string with yaml format"""
    _content = """- Lorem
- ipsum
- sit
- amet
"""
    return _content


@pytest.fixture
def csv_file_path(fixtures_dir: Path) -> Path:
    """Return a file path to example CSV file."""
    return Path(fixtures_dir, "io", "example.csv")


@pytest.fixture
def tsv_file_path(fixtures_dir: Path) -> Path:
    """Return a file path to example TSV file."""
    return Path(fixtures_dir, "io", "example.tsv")


@pytest.fixture
def txt_file_path(fixtures_dir: Path) -> Path:
    """Return a file path to example TXT file."""
    return Path(fixtures_dir, "io", "example.txt")


@pytest.fixture
def tsv_stream() -> str:
    """Return string with TSV format."""
    return """Lorem	ipsum	sit	amet"""


@pytest.fixture
def csv_stream() -> str:
    """Return string with CSV format."""
    return """Lorem,ipsum,sit,amet"""


@pytest.fixture
def csv_temp_path(cg_dir: Path) -> Path:
    """Return a temp file path to use when writing csv."""
    return Path(cg_dir, "write.csv")


@pytest.fixture
def tsv_temp_path(cg_dir: Path) -> Path:
    """Return a temp file path to use when writing csv."""
    return Path(cg_dir, "write.tsv")


@pytest.fixture
def xml_file_path(fixtures_dir: Path) -> Path:
    """Return a file path to example XML file."""
    return Path(fixtures_dir, "io", "example_xml.xml")


@pytest.fixture
def xml_temp_path(cg_dir: Path) -> Path:
    """Return a temp file path to use when writing xml."""
    return Path(cg_dir, "write_xml.xml")
