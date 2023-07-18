from pathlib import Path
from typing import List

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.archive.archive import ArchiveAPI, FileData
from cg.store.models import Sample


def test_archive_samples(
    archive_api: ArchiveAPI, populated_housekeeper_api: HousekeeperAPI, sample_id: str
):
    # GIVEN a list of sample ids whit housekeeper bundles and SPRING files
    sample: Sample = archive_api.status_db.get_sample_by_internal_id(sample_id)
    # WHEN archiving these samples
    archive_api.archive_samples(samples=[sample])
    # THEN tha archive objects should be added to housekeeper along with a task_id

    assert (
        populated_housekeeper_api.files(
            bundle=sample.internal_id, tags={SequencingFileTag.SPRING, sample.internal_id}
        )
        .first()
        .archive
    )


def test_sort_spring_files_on_archive_location(
    archive_api: ArchiveAPI, populated_housekeeper_api: HousekeeperAPI
):
    # GIVEN a populated status_db database with two customers, one DDN and one non-DDN,
    # with the DDN customer having two samples, and the non-DDN having one sample.

    # WHEN fetching all non-archived spring files
    # When sorting the returned files on the data archive locations of the customers
    sorted_spring_files: List[FileData] = archive_api.add_archive_location_to_files(
        [
            FileData(file=file, sample_internal_id=sample)
            for sample, file in populated_housekeeper_api.get_non_archived_spring_path_and_bundle_name()
        ]
    )

    assert len(sorted_spring_files["DDN"]) == 1


def test_archive_all_non_archived_spring_files(
    archive_api: ArchiveAPI, populated_housekeeper_api: HousekeeperAPI, spring_file: Path
):
    assert False


def test_retrieve_sample():
    assert False
