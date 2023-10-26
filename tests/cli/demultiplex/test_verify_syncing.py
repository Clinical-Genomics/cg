from pathlib import Path
from unittest import mock

from cg.cli.demultiplex.demux import create_manifest_files


def test_create_manifest_files_true(tmp_path: Path, cli_runner):
    # GIVEN two flowcell directories
    flow_cell_directories = [Path(tmp_path, "flowcell1"), Path(tmp_path, "flowcell2")]
    for directory in flow_cell_directories:
        directory.mkdir()

    # GIVEN that both flowcell directories need a manifest file
    with mock.patch("cg.cli.demultiplex.demux.needs_manifest_file", return_value=True):
        with mock.patch(
            "cg.cli.demultiplex.demux.create_manifest_file", return_value=None
        ) as manifest_creation:
            # WHEN creating manifest files
            cli_runner.invoke(cli=create_manifest_files, args=["-s", tmp_path.as_posix()])

    # THEN the manifest files creation should be called for every flowcell directory
    assert manifest_creation.call_count == len(flow_cell_directories)


def test_create_manifest_files_false(tmp_path: Path, cli_runner):
    # GIVEN two flowcell directories
    flow_cell_directories = [Path(tmp_path, "flowcell1"), Path(tmp_path, "flowcell2")]
    for directory in flow_cell_directories:
        directory.mkdir()

    # GIVEN that none of the flowcell directories need a manifest file
    with mock.patch("cg.cli.demultiplex.demux.needs_manifest_file", return_value=False):
        with mock.patch(
            "cg.cli.demultiplex.demux.create_manifest_file", return_value=None
        ) as manifest_creation:
            # WHEN creating manifest files
            cli_runner.invoke(cli=create_manifest_files, args=["-s", tmp_path.as_posix()])

    # THEN the manifest files creation should not be called
    assert not manifest_creation.called
