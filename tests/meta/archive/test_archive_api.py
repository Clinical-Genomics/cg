from typing import List

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.archiving import ArchiveLocationsInUse
from cg.meta.archive.archive import ArchiveAPI, PathAndSample
from cg.store.models import Sample


def test_get_files_by_archive_location(
    archive_api: ArchiveAPI, populated_housekeeper_api: HousekeeperAPI
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
    sorted_spring_files: List[PathAndSample] = archive_api.get_files_by_archive_location(
        non_archived_spring_files, archive_location=ArchiveLocationsInUse.KAROLINSKA_BUCKET
    )

    # THEN there should be spring files
    assert sorted_spring_files
    for file_and_sample in sorted_spring_files:
        sample: Sample = archive_api.status_db.get_sample_by_internal_id(
            file_and_sample.sample_internal_id
        )
        # THEN each file should be correctly sorted on its archive location
        assert sample.customer.data_archive_location == ArchiveLocationsInUse.KAROLINSKA_BUCKET
