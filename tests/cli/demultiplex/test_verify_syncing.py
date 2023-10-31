import shutil
from pathlib import Path

from cg.cli.demultiplex.demux import create_manifest_files
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.io.csv import read_csv
from tests.meta.demultiplex.conftest import get_all_files_in_directory_tree


def test_create_manifest_files_true(
    cli_runner, tmp_flow_cells_directory_ready_for_demultiplexing_bcl_convert: Path
):
    # GIVEN two flowcell directories
    first_flowcell_directory: Path = tmp_flow_cells_directory_ready_for_demultiplexing_bcl_convert
    second_flowcell_directory = Path(
        shutil.copytree(
            first_flowcell_directory,
            Path(
                tmp_flow_cells_directory_ready_for_demultiplexing_bcl_convert.parent, "flowcell_2"
            ),
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

        all_files_in_directory: list[Path] = get_all_files_in_directory_tree(flow_cell)
        all_files_in_directory.remove(Path(manifest_file.name))
        files_in_manifest: list[Path] = [
            Path(file[0].strip()) for file in read_csv(delimiter="\t", file_path=manifest_file)
        ]

        # THEN the manifest file should contain all files in the flowcell directory
        for file in all_files_in_directory:
            assert file in files_in_manifest


def test_create_manifest_files_false(
    cli_runner, tmp_flow_cells_directory_ready_for_demultiplexing_bcl_convert: Path
):
    # GIVEN two flowcell directories with missing CopyComplete.txt
    first_flowcell_directory = tmp_flow_cells_directory_ready_for_demultiplexing_bcl_convert
    Path(first_flowcell_directory, DemultiplexingDirsAndFiles.COPY_COMPLETE).unlink()
    second_flowcell_directory = Path(
        shutil.copytree(
            first_flowcell_directory,
            Path(
                tmp_flow_cells_directory_ready_for_demultiplexing_bcl_convert.parent, "flowcell_2"
            ),
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
