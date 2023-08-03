from pathlib import Path
from typing import List

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.archiving import ArchiveLocationsInUse
from cg.meta.archive.archive import SpringArchiveAPI, PathAndSample
from cg.store.models import Sample


def test_get_files_by_archive_location(
    spring_archive_api: SpringArchiveAPI, populated_housekeeper_api: HousekeeperAPI
):
    """Tests the fetching of sample/customer info from statusdb based on bundle_names
    and returning the samples with the given Archive location."""
    # GIVEN a populated status_db database with two customers, one DDN and one non-DDN,
    # with the DDN customer having two samples, and the non-DDN having one sample.

    # Given non-archived spring files
    non_archived_spring_files: List[PathAndSample] = [
        PathAndSample(path=path, sample_internal_id=sample)
        for sample, path in populated_housekeeper_api.get_non_archived_spring_path_and_bundle_name()
    ]
    # WHEN extracting the files based on data archive
    sorted_spring_files: List[PathAndSample] = spring_archive_api.get_files_by_archive_location(
        non_archived_spring_files, archive_location=ArchiveLocationsInUse.KAROLINSKA_BUCKET
    )

    # THEN there should be spring files
    assert sorted_spring_files
    for file_and_sample in sorted_spring_files:
        sample: Sample = spring_archive_api.status_db.get_sample_by_internal_id(
            file_and_sample.sample_internal_id
        )
        # THEN each file should be correctly sorted on its archive location
        assert sample.customer.data_archive_location == ArchiveLocationsInUse.KAROLINSKA_BUCKET


def test_get_sample_exists(sample_id: str, spring_archive_api: SpringArchiveAPI, spring_file: Path):
    """Tests fetching a sample when the sample exists."""
    # GIVEN a sample that exists in the database
    file_info: PathAndSample = PathAndSample(spring_file, sample_id)

    # WHEN getting the sample
    sample: Sample = spring_archive_api.get_sample(file_info)

    # THEN the correct sample should be returned
    assert sample.internal_id == sample_id


def test_get_sample_not_exists(caplog, spring_archive_api: SpringArchiveAPI, spring_file: Path):
    """Tests fetching a sample when the sample does not exist."""
    # GIVEN a sample that does not exist in the database
    sample_id: str = "non-existent-sample"
    file_info: PathAndSample = PathAndSample(spring_file, sample_id)

    # WHEN getting the sample
    sample: Sample = spring_archive_api.get_sample(file_info)

    # THEN the no sample should be returned
    # THEN both sample_id and file path should be logged
    assert not sample
    assert sample_id in caplog.text
    assert spring_file.as_posix() in caplog.text
