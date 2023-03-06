from pathlib import Path
from typing import Dict, List

from cg.meta.archive.ddn import DDNApi


def test__format_paths_archive(ddn_api: DDNApi, local_directory: Path, remote_directory: Path):
    """Tests the formatting function of the path dict for archiving."""
    # GIVEN a source path and a destination path

    # WHEN creating the correctly formatted dictionary
    formatted_data: List[Dict[str, str]] = ddn_api._format_paths_archive(
        {local_directory: remote_directory}
    )

    # THEN the output should be a list
    assert isinstance(formatted_data, list)

    # THEN the source path should be the local directory minus the /home part
    assert (
        formatted_data[0].get("source")
        == Path(ddn_api.local_storage, *local_directory.parts[2:]).as_posix()
    )
    # THEN the destination path should be the remote directory
    assert (
        formatted_data[0].get("destination")
        == ddn_api.archive_repository + remote_directory.as_posix()
    )


def test__format_paths_retrieve(ddn_api: DDNApi, local_directory: Path, remote_directory: Path):
    """Tests the formatting function of the path dict for retrieving."""
    # GIVEN a source path and a destination path

    # WHEN creating the correctly formatted dictionary
    formatted_data: List[Dict[str, str]] = ddn_api._format_paths_retrieve(
        {remote_directory: local_directory}
    )

    # THEN the output should be a list
    assert isinstance(formatted_data, list)

    # THEN the destination path should be the local directory minus the /home part
    assert (
        formatted_data[0].get("destination")
        == Path(ddn_api.local_storage, *local_directory.parts[2:]).as_posix()
    )

    # THEN the source path should be the remote directory
    assert (
        formatted_data[0].get("source") == ddn_api.archive_repository + remote_directory.as_posix()
    )
