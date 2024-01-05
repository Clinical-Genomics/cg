import shutil
from pathlib import Path

from cg.cli.demultiplex.demux import (
    confirm_transfer_of_illumina_flow_cell,
    confirm_transfer_of_nanopore_flow_cell,
    create_manifest_files,
)
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.nanopore_files import NanoporeDirsAndFiles
from cg.io.csv import read_csv
from cg.meta.demultiplex.utils import (
    create_manifest_file,
    get_nanopore_flow_cell_directories,
    get_nanopore_flow_cell_relative_path,
)
from cg.models.cg_config import CGConfig
from cg.utils.files import get_directories_in_path
from tests.meta.demultiplex.conftest import get_all_files_in_directory_tree

THREE_LEVELS_DOWN = "*/*/*"


def test_create_manifest_files_true(
    cli_runner, tmp_flow_cells_directory_ready_for_demultiplexing_bcl_convert: Path
):
    """Test that manifest files are created for flow cells where the sequencing is complete."""
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

        # THEN the manifest file should contain all files in the flowcell directory
        assert_manifest_file_contains_all_files(
            manifest_file=manifest_file, directory_of_interest=flow_cell
        )


def test_create_manifest_files_false(
    cli_runner, tmp_flow_cells_directory_ready_for_demultiplexing_bcl_convert: Path
):
    """Test that manifest files are not created for flow cells where the sequencing is not complete."""
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


def test_confirm_transfer_of_illumina_flow_cell_all_files_present(
    cg_config_object: CGConfig,
    cli_runner,
    bcl_convert_flow_cell_dir: Path,
    novaseq_x_flow_cell_directory: Path,
    tmp_path: Path,
):
    # GIVEN source and target directories with two flow cells
    source_directory, target_directory = set_up_source_and_target_directories(
        folders_to_include=[bcl_convert_flow_cell_dir, novaseq_x_flow_cell_directory],
        temporary_path=tmp_path,
    )
    cg_config_object.flow_cells_dir = target_directory.as_posix()
    for flow_cell in [bcl_convert_flow_cell_dir, novaseq_x_flow_cell_directory]:
        # GIVEN that they all files are present except the copy complete file
        Path(target_directory, flow_cell.name, DemultiplexingDirsAndFiles.COPY_COMPLETE).unlink(
            missing_ok=True
        )
        # GIVEN that they each have manifest files
        create_manifest_file(Path(source_directory, flow_cell.name))

    # WHEN checking if all files are present
    result = cli_runner.invoke(
        cli=confirm_transfer_of_illumina_flow_cell,
        args=["--source-directory", source_directory.as_posix()],
        obj=cg_config_object,
    )

    # THEN the command should exit successfully
    assert result.exit_code == 0

    # THEN a copy complete file should be created
    assert all(
        Path(flow_cell, DemultiplexingDirsAndFiles.COPY_COMPLETE).exists()
        for flow_cell in [
            Path(target_directory, bcl_convert_flow_cell_dir.name),
            Path(target_directory, novaseq_x_flow_cell_directory.name),
        ]
    )


def test_confirm_transfer_of_illumina_flow_cell_missing_files(
    cg_config_object: CGConfig,
    cli_runner,
    bcl_convert_flow_cell_dir: Path,
    novaseq_x_flow_cell_directory: Path,
    tmp_path: Path,
):
    # GIVEN source and target directories with two flow cells
    source_directory, target_directory = set_up_source_and_target_directories(
        folders_to_include=[bcl_convert_flow_cell_dir, novaseq_x_flow_cell_directory],
        temporary_path=tmp_path,
    )
    cg_config_object.flow_cells_dir = target_directory.as_posix()
    for flow_cell in [bcl_convert_flow_cell_dir, novaseq_x_flow_cell_directory]:
        Path(target_directory, flow_cell.name, DemultiplexingDirsAndFiles.COPY_COMPLETE).unlink(
            missing_ok=True
        )
        # GIVEN that a file is missing
        Path(
            target_directory, flow_cell.name, DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE
        ).unlink()
        # GIVEN that they each have manifest files
        create_manifest_file(Path(source_directory, flow_cell.name))

    # WHEN checking if all files are present
    result = cli_runner.invoke(
        cli=confirm_transfer_of_illumina_flow_cell,
        args=["--source-directory", source_directory.as_posix()],
        obj=cg_config_object,
    )

    # THEN the command should exit successfully
    assert result.exit_code == 0

    # THEN a copy complete file should be created
    assert all(
        not Path(flow_cell, DemultiplexingDirsAndFiles.COPY_COMPLETE).exists()
        for flow_cell in [
            Path(target_directory, bcl_convert_flow_cell_dir.name),
            Path(target_directory, novaseq_x_flow_cell_directory.name),
        ]
    )


def test_confirm_transfer_of_nanopore_flow_cell_all_files_present(
    cg_config_object, cli_runner, nanopore_flow_cells_dir: Path, tmp_path: Path
):
    # GIVEN a Nanopore run with two samples
    experiment_directories: list[Path] = get_directories_in_path(nanopore_flow_cells_dir)
    flow_cell_directories: list[Path] = get_nanopore_flow_cell_directories(nanopore_flow_cells_dir)

    source_directory, target_directory = set_up_source_and_target_directories(
        folders_to_include=experiment_directories,
        temporary_path=tmp_path,
    )
    cg_config_object.nanopore_data_directory = target_directory.as_posix()
    Path(target_directory, NanoporeDirsAndFiles.SYSTEMD_TRIGGER_DIRECTORY).mkdir()
    for flow_cell_directory in get_nanopore_flow_cell_directories(source_directory):
        # GIVEN that no file is missing
        # GIVEN that they each have manifest files
        create_manifest_file(flow_cell_directory)

    # WHEN checking if all files are present
    result = cli_runner.invoke(
        cli=confirm_transfer_of_nanopore_flow_cell,
        args=["--source-directory", source_directory.as_posix()],
        obj=cg_config_object,
    )
    # THEN the command should exit successfully
    assert result.exit_code == 0

    # THEN a copy complete file should be created
    assert all(
        Path(
            target_directory,
            get_nanopore_flow_cell_relative_path(flow_cell_directory),
            DemultiplexingDirsAndFiles.COPY_COMPLETE,
        ).exists()
        for flow_cell_directory in flow_cell_directories
    )

    # THEN a trigger file should be created
    assert all(
        Path(
            target_directory,
            NanoporeDirsAndFiles.SYSTEMD_TRIGGER_DIRECTORY,
            flow_cell_directory.name,
        ).exists()
        for flow_cell_directory in flow_cell_directories
    )


def test_confirm_transfer_of_nanopore_flow_cell_missing_files(
    cg_config_object, cli_runner, nanopore_flow_cells_dir: Path, tmp_path: Path
):
    # GIVEN a Nanopore run with two samples
    experiment_directories: list[Path] = get_directories_in_path(nanopore_flow_cells_dir)
    flow_cell_directories: list[Path] = get_nanopore_flow_cell_directories(nanopore_flow_cells_dir)
    source_directory, target_directory = set_up_source_and_target_directories(
        folders_to_include=experiment_directories,
        temporary_path=tmp_path,
    )
    cg_config_object.nanopore_data_directory = target_directory.as_posix()
    Path(target_directory, NanoporeDirsAndFiles.SYSTEMD_TRIGGER_DIRECTORY).mkdir()
    for flow_cell_directory in get_nanopore_flow_cell_directories(source_directory):
        # GIVEN that a file is missing
        list(
            Path(target_directory, get_nanopore_flow_cell_relative_path(flow_cell_directory)).glob(
                "*txt"
            )
        )[0].unlink()
        # GIVEN that they each have manifest files
        create_manifest_file(flow_cell_directory)

    # WHEN checking if all files are present
    result = cli_runner.invoke(
        cli=confirm_transfer_of_nanopore_flow_cell,
        args=["--source-directory", source_directory.as_posix()],
        obj=cg_config_object,
    )

    # THEN the command should exit successfully
    assert result.exit_code == 0

    # THEN no copy complete file should be created
    assert all(
        not Path(
            target_directory,
            flow_cell_directory.parent.name,
            flow_cell_directory.name,
            DemultiplexingDirsAndFiles.COPY_COMPLETE,
        ).exists()
        for flow_cell_directory in flow_cell_directories
    )

    # THEN no trigger file should be created
    assert all(
        not Path(
            target_directory,
            get_nanopore_flow_cell_relative_path(flow_cell_directory),
            DemultiplexingDirsAndFiles.COPY_COMPLETE,
        ).exists()
        for flow_cell_directory in flow_cell_directories
    )


def set_up_source_and_target_directories(
    folders_to_include: list[Path], temporary_path: Path
) -> tuple[Path, Path]:
    source_directory = Path(temporary_path, "source")
    target_directory = Path(temporary_path, "target")
    source_directory.mkdir()
    target_directory.mkdir()
    for flow_cell in folders_to_include:
        shutil.copytree(flow_cell, Path(source_directory, flow_cell.name))
        shutil.copytree(flow_cell, Path(target_directory, flow_cell.name))
    return source_directory, target_directory
