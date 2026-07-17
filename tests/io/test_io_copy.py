from pathlib import Path

from cg.io.copy import copy_file


def test_copy_file_to_directory(fixtures_dir: Path, tmp_path: Path):
    # GIVEN a source file
    file: Path = Path(fixtures_dir, "io", "copy.txt")

    # GIVEN a target dir
    directory: Path = tmp_path

    # WHEN copying file to directory
    copy_file(from_path=file, to_path=directory)

    # THEN new copy and the copied file should exist
    assert file.is_file()
    assert directory.joinpath(file.name).is_file()
    assert directory.joinpath(file.name).read_bytes() == file.read_bytes()


def test_copy_file_to_file(fixtures_dir: Path, tmp_path: Path):
    # GIVEN a source file
    file: Path = Path(fixtures_dir, "io", "copy.txt")

    # GIVEN a target file
    target_file: Path = tmp_path / "renamed_copy.txt"

    # WHEN copying file to specific file path
    copy_file(from_path=file, to_path=target_file)

    # THEN the file and the target file should exist at the exact target path
    assert file.is_file()
    assert target_file.is_file()
    assert target_file.read_bytes() == file.read_bytes()
