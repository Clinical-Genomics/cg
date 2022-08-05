from pathlib import Path

import pytest


@pytest.fixture(name="yaml_stream")
def yaml_stream() -> str:
    """Return string with yaml format"""
    _content = """- Lorem
- ipsum
- sit
- amet
"""
    return _content


@pytest.fixture(name="invalid_yaml_file")
def invalid_yaml_file(project_dir: Path) -> Path:
    """Return path for invalid yaml file"""
    content = """a: b: c"""
    invalid_yaml: Path = Path(project_dir, "invalid_yaml_file.txt")
    with open(invalid_yaml, "w") as outfile:
        outfile.write(content)
    return invalid_yaml
