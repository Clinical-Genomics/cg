import shutil
from pathlib import Path

import pytest


@pytest.fixture
def zip_base_path(tmp_path: Path) -> Path:
    zip_base = Path(tmp_path, "zip_base")
    zip_base.mkdir()
    return zip_base


@pytest.fixture
def file_in_zip(zip_base_path: Path) -> Path:
    zipped_file = Path(zip_base_path, "zipped_file.txt")
    zipped_file.touch()
    return zipped_file


@pytest.fixture
def zipped_folder(zip_base_path: Path, file_in_zip: Path, tmp_path) -> Path:
    assert file_in_zip.exists()
    zip_out = Path(tmp_path, "zipped_folder")
    shutil.make_archive(zip_out.as_posix(), format="zip", root_dir=zip_base_path.as_posix())
    return Path(zip_out.as_posix() + ".zip")


@pytest.fixture
def destination_folder(tmp_path: Path) -> Path:
    return Path(tmp_path, "destination_folder")
