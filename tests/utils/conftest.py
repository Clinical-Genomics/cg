"""Fixtures for utils"""

from pathlib import Path

import pytest

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
        "uri:mongodb://None@localhost:27017\n"
        "2018-11-29 08:41:38 130-229-8-20-dhcp.local "
        "mongo_adapter.client[77135] INFO Connection "
        "established\n"
    )
    return lines


@pytest.fixture(scope="session")
def some_file() -> str:
    """Return a file."""
    return "some_file.txt"


@pytest.fixture(scope="session")
def nested_directory_with_file(tmp_path_factory, some_file: str) -> Path:
    """Return a nested directory with a file."""
    directory = tmp_path_factory.mktemp("nested_directory_with_file")
    sub_directory = directory / "sub_directory"
    sub_directory.mkdir()
    file = sub_directory / some_file
    file.touch()
    return directory


@pytest.fixture(scope="session")
def path_with_directories_and_a_file(
    tmp_path_factory, sub_dir_names: list[str], some_file: str
) -> Path:
    """Return a path with directories and a file in it."""
    directory: Path = tmp_path_factory.mktemp("tmp_dir")
    for sub_dir_name in sub_dir_names:
        sub_dir: Path = Path(directory, sub_dir_name)
        sub_dir.mkdir()
    file = Path(directory, some_file)
    file.touch()
    return directory


@pytest.fixture(scope="session")
def sub_dir_names() -> list[str]:
    return ["sub_dir_1", "sub_dir_2", "sub_dir_3"]
