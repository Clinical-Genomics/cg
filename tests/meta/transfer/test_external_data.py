"""Tests for the transfer of external data"""
from pathlib import Path
import datetime as dt
from os import utime

from housekeeper.store.models import Version


from cg.meta.external_data import ExternalDataHandler
from cg.store.models import Sample


def test_is_recent_file_true(project_dir: Path):
    # GIVEN a recent directory
    project_dir.touch(exist_ok=True)

    # WHEN the timestamp is checked
    is_recent: bool = ExternalDataHandler.is_recent_file_system_entry(file_system_entry=project_dir)

    # THEN it should return a True response
    assert is_recent


def test_is_recent_file_false(project_dir: Path):
    # GIVEN a file older than 4 hours
    project_dir.touch()
    utime(
        path=project_dir,
        ns=(
            (dt.datetime.now() - dt.timedelta(hours=5)).microsecond * 1000,
            (dt.datetime.now() - dt.timedelta(hours=5)).microsecond * 1000,
        ),
    ),

    # WHEN the timestamp is checked
    is_recent: bool = ExternalDataHandler.is_recent_file_system_entry(file_system_entry=project_dir)

    # THEN it should return a False response
    assert not is_recent


def test_add_sample_to_hk(
    external_data_handler: ExternalDataHandler,
    external_data_sample_folder: Path,
    sample: Sample,
):
    # GIVEN a sample_folder with associated
    # GIVEN that the sample does not exist in Housekeeper
    assert not external_data_handler.hk_api.file_exists(sample.internal_id)
    external_data_handler.hk_api._last_version = False

    # WHEN a sample is added to Housekeeper
    external_data_handler.add_sample_to_hk(sample=sample, sample_folder=external_data_sample_folder)

    # THEN there should be a bundle with those files added
    version: Version = external_data_handler.hk_api._version_obj
    assert version
    assert version.files
    assert all(
        Path(file.path) in list(external_data_sample_folder.iterdir()) for file in version.files
    )


def test_curate_external_folder(
    external_data_directory: Path, external_data_handler: ExternalDataHandler
):
    # GIVEN an external_data_directory with samples not added to housekeeper
    assert not external_data_handler.hk_api.files()
    assert all(
        sample_folder.name in [sample.name for sample in external_data_handler.status_db.samples()]
        for customer_folder in external_data_directory.iterdir()
        for sample_folder in customer_folder.iterdir()
    )

    # WHEN the external data folder is curated
    external_data_handler.curate_external_folder()

    # THEN the files should be added to housekeeper
    assert all(
        str(file) in [hk_file.path for hk_file in external_data_handler.hk_api.files()]
        for customer_folder in external_data_directory.iterdir()
        for sample_folder in customer_folder.iterdir()
        for file in sample_folder.iterdir()
    )

    # THEN the sample folder should have been renamed
    assert all(
        sample_folder.name
        in [sample.internal_id for sample in external_data_handler.status_db.samples()]
        for customer_folder in external_data_directory.iterdir()
        for sample_folder in customer_folder.iterdir()
    )
