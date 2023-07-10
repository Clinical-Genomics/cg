"""Fixtures for utils"""

import pytest
from pathlib import Path
from cg.utils import Process


@pytest.fixture(scope="function")
def ls_process():
    """
    list files process
    """
    binary = "ls"
    process = Process(binary=binary)
    return process


@pytest.fixture(scope="function")
def stderr_output():
    """
    std err lines
    """
    lines = (
        "2018-11-29 08:41:38 130-229-8-20-dhcp.local "
        "mongo_adapter.client[77135] INFO Connecting to "
        "uri:mongodb://None:None@localhost:27017\n"
        "2018-11-29 08:41:38 130-229-8-20-dhcp.local "
        "mongo_adapter.client[77135] INFO Connection "
        "established\n"
    )
    return lines


@pytest.fixture(name="some_file", scope="session")
def fixture_some_file() -> str:
    """Return a file."""
    return "some_file.txt"


@pytest.fixture(name="nested_directory_with_file", scope="session")
def fixture_nested_directory_with_file(tmp_path_factory, some_file: str) -> Path:
    """Return a nested directory with a file."""
    directory = tmp_path_factory.mktemp("nested_directory_with_file")
    sub_directory = directory / "sub_directory"
    sub_directory.mkdir()
    file = sub_directory / some_file
    file.touch()
    return directory
