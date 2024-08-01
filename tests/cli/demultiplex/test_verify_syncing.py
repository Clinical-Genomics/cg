import shutil
from pathlib import Path

from cg.cli.demultiplex.demux import create_manifest_files
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.io.csv import read_csv
from cg.utils.files import get_all_files_in_directory_tree


def test_create_manifest_files_true(
    cli_runner, tmp_flow_cells_directory_ready_for_demultiplexing: Path
):
    """Test that manifest files are created for flow cells where the sequencing is complete."""
    # GIVEN two flowcell directories
    first_flowcell_directory: Path = tmp_flow_cells_directory_ready_for_demultiplexing
    second_flowcell_directory = Path(
        shutil.copytree(
            first_flowcell_directory,
            Path(tmp_flow_cells_directory_ready_for_demultiplexing.parent, "flowcell_2"),
        )
    )

    # WHEN creating manifest files
    cli_runner.invoke(
        cli=create_manifest_files,
        args=["--source-directory", first_flowcell_directory.parent.as_posix()],
    )

    for flow_cell in [first_flowcell_directory, second_flowcell_directory]:
        manifest_file = Path(flow_cell, DemultiplexingDirsAndFiles.CG_FILE_MANIFEST)

        # THEN the manifest file should exist
        assert manifest_file.exists()

        # THEN the manifest file should contain all files in the flowcell directory
        assert_manifest_file_contains_all_files(
            manifest_file=manifest_file, directory_of_interest=flow_cell
        )


def test_create_manifest_files_false(
    cli_runner, tmp_flow_cells_directory_ready_for_demultiplexing: Path
):
    """Test that manifest files are not created for flow cells where the sequencing is not complete."""
    # GIVEN two flowcell directories with missing CopyComplete.txt
    first_flowcell_directory = tmp_flow_cells_directory_ready_for_demultiplexing
    Path(first_flowcell_directory, DemultiplexingDirsAndFiles.COPY_COMPLETE).unlink()
    second_flowcell_directory = Path(
        shutil.copytree(
            first_flowcell_directory,
            Path(tmp_flow_cells_directory_ready_for_demultiplexing.parent, "flowcell_2"),
        )
    )

    # WHEN creating manifest files
    cli_runner.invoke(
        cli=create_manifest_files,
        args=["--source-directory", first_flowcell_directory.parent.as_posix()],
    )

    for flow_cell in [first_flowcell_directory, second_flowcell_directory]:
        manifest_file = Path(flow_cell, DemultiplexingDirsAndFiles.CG_FILE_MANIFEST)

        # THEN the manifest file should not exist
        assert not manifest_file.exists()


def test_create_manifest_files_true_nanopore_data(
    cli_runner, nanopore_flow_cells_dir: Path, tmp_path
):
    """Test that manifest files are created for flow cells where the sequencing is complete."""
    # GIVEN a Nanopore run with two samples
    tmp_nanopore_directory = Path(
        shutil.copytree(
            nanopore_flow_cells_dir, Path(tmp_path, nanopore_flow_cells_dir.name).as_posix()
        )
    )
    sample_directories: list[Path] = list(Path(tmp_nanopore_directory).glob("*/*/*"))
    assert len(sample_directories) == 2

    # WHEN creating manifest files
    cli_runner.invoke(
        cli=create_manifest_files,
        args=["--source-directory", f"{tmp_nanopore_directory}/*/*"],
    )

    for sample_directory in sample_directories:
        manifest_file = Path(sample_directory, DemultiplexingDirsAndFiles.CG_FILE_MANIFEST)

        # THEN the manifest file should exist
        assert manifest_file.exists()

        # THEN the manifest file should contain all files in the flowcell directory
        assert_manifest_file_contains_all_files(
            manifest_file=manifest_file, directory_of_interest=sample_directory
        )


def assert_manifest_file_contains_all_files(
    manifest_file: Path, directory_of_interest: Path
) -> None:
    """Assert that the manifest file contains all files in the directory of interest."""
    all_files_in_directory: list[Path] = get_all_files_in_directory_tree(directory_of_interest)
    all_files_in_directory.remove(Path(manifest_file.name))
    files_in_manifest: list[Path] = [
        Path(file[0].strip()) for file in read_csv(delimiter="\t", file_path=manifest_file)
    ]
    assert all(file in files_in_manifest for file in all_files_in_directory)
