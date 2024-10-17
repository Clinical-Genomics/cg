from pathlib import Path

from cg.services.run_devices.run_names.pacbio import PacbioRunNamesService


def test_pacbio_get_run_names(
    pacbio_run_names_service: PacbioRunNamesService, pacbio_run_names: set
):
    """Test that getting PacBio run names works."""
    # GIVEN a PacBio run names service

    # WHEN getting the run names
    run_names: list[str] = pacbio_run_names_service.get_run_names()

    # THEN the run names are returned
    assert set(run_names) == pacbio_run_names


def test_pacbio_get_run_names_empty(tmp_path: Path):
    # GIVEN a run directory with no run folders and a PacBio run names service
    pacbio_run_names_service: PacbioRunNamesService = PacbioRunNamesService(
        run_directory=tmp_path.as_posix()
    )

    # WHEN getting the run names
    run_names: list[str] = pacbio_run_names_service.get_run_names()

    # THEN no run names are returned
    assert run_names == []


def test_pacbio_get_run_names_with_files_return_emty(tmp_path: Path):
    # GIVEN a run directory with files and a PacBio run names service
    run_dir = Path(tmp_path, "run")
    run_dir.mkdir()
    Path(run_dir, "file1").touch()
    Path(run_dir, "file2").touch()
    pacbio_run_names_service: PacbioRunNamesService = PacbioRunNamesService(
        run_directory=run_dir.as_posix()
    )

    # WHEN getting the run names
    run_names: list[str] = pacbio_run_names_service.get_run_names()

    # THEN no run names are returned
    assert run_names == []


def test_pacbio_get_run_names_with_subfolders_return_empty(tmp_path: Path):
    # GIVEN a run directory with an empty subfolder and a PacBio run names service
    run_dir = Path(tmp_path, "run")
    run_dir.mkdir()
    subfolder = Path(run_dir, "subfolder")
    subfolder.mkdir()
    pacbio_run_names_service: PacbioRunNamesService = PacbioRunNamesService(
        run_directory=run_dir.as_posix()
    )

    # WHEN getting the run names
    run_names: list[str] = pacbio_run_names_service.get_run_names()

    # THEN no run names are returned
    assert run_names == []
