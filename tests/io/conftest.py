from pathlib import Path

import pytest


@pytest.fixture(name="json_stream")
def fixture_json_stream() -> str:
    """Return string with json format"""
    _content = """{"Lorem": {"ipsum": "sit"}}"""
    return _content


@pytest.fixture(name="json_file_path")
def fixture_json_file_path(fixtures_dir: Path) -> Path:
    """Return a file path to example json file"""
    return Path(fixtures_dir, "io", "example_json.json")


@pytest.fixture(name="json_temp_path")
def fixture_json_temp_path(cg_dir: Path) -> Path:
    """Return a temp file path to use when writing json"""
    return Path(cg_dir, "write_json.json")


@pytest.fixture(name="yaml_stream")
def fixture_yaml_stream() -> str:
    """Return string with yaml format"""
    _content = """- Lorem
- ipsum
- sit
- amet
"""
    return _content


@pytest.fixture(name="csv_file_path")
def fixture_csv_file_path(fixtures_dir: Path) -> Path:
    """Return a file path to example CSV file."""
    return Path(fixtures_dir, "io", "example_csv.csv")


@pytest.fixture(name="csv_stream")
def fixture_csv_stream() -> str:
    """Return string with CSV format."""
    return """Lorem,ipsum,sit,amet"""


@pytest.fixture(name="csv_temp_path")
def fixture_csv_temp_path(cg_dir: Path) -> Path:
    """Return a temp file path to use when writing csv."""
    return Path(cg_dir, "write_csv.csv")


@pytest.fixture(name="xml_file_path")
def fixture_xml_file_path(fixtures_dir: Path) -> Path:
    """Return a file path to example XML file."""
    return Path(fixtures_dir, "io", "example_xml.xml")


@pytest.fixture(name="xml_temp_path")
def fixture_xml_temp_path(cg_dir: Path) -> Path:
    """Return a temp file path to use when writing xml."""
    return Path(cg_dir, "write_xml.xml")
