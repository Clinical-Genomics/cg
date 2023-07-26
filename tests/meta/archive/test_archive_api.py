from typing import List, Dict

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.archive.archive import ArchiveAPI, PathAndSample
from cg.store.models import Sample


def test_sort_spring_files_on_archive_location(
    archive_api: ArchiveAPI, populated_housekeeper_api: HousekeeperAPI
):
    # GIVEN a populated status_db database with two customers, one DDN and one non-DDN,
    # with the DDN customer having two samples, and the non-DDN having one sample.

    # WHEN fetching all non-archived spring files
    non_archived_spring_files: List[PathAndSample] = [
        PathAndSample(path=path, sample_internal_id=sample)
        for sample, path in populated_housekeeper_api.get_non_archived_spring_path_and_bundle_name()
    ]
    # WHEN sorting the returned files on the data archive locations of the customers
    sorted_spring_files: Dict[
        str, List[PathAndSample]
    ] = archive_api.sort_files_on_archive_location(non_archived_spring_files)

    # THEN there should be spring files
    assert sorted_spring_files
    for archive_location, files_and_samples in sorted_spring_files.items():
        assert files_and_samples
        for file_and_sample in files_and_samples:
            sample: Sample = archive_api.status_db.get_sample_by_internal_id(
                file_and_sample.sample_internal_id
            )
            # THEN then each file should be correctly sorted on it's archive location
            assert sample.customer.data_archive_location == archive_location
