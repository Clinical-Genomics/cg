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


@pytest.fixture(name="invalid_yaml_file")
def fixture_invalid_yaml_file(project_dir: Path) -> Path:
    """Return path for invalid yaml file"""
    content = """a: b: c"""
    invalid_yaml: Path = Path(project_dir, "invalid_yaml_file.txt")
    with open(invalid_yaml, "w") as outfile:
        outfile.write(content)
    return invalid_yaml
