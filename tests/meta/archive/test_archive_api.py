from pathlib import Path
from typing import Dict, List

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.archive.archive import ArchiveAPI, ArchiveLocationAndSample, SampleAndFile
from cg.store.models import Sample
from housekeeper.store.models import File


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


def test_get_sample_id_from_file(archive_api: ArchiveAPI, spring_file: Path):
    # GIVEN a spring file related to sample ADM1
    # WHEN fetching the sample id from the spring file path
    sample_id: str = archive_api.get_sample_id_from_file_path(file_path=spring_file.as_posix())
    # THEN the sample id returned should be ADM1
    assert sample_id == "ADM1"


def test_get_archive_location_and_sample_id_from_file_path(
    archive_api: ArchiveAPI, spring_file: Path
):
    # GIVEN a spring file related to sample ADM1 belonging to a DDN Customer

    # WHEN fetching the archive location and sample id from the spring file path
    archive_location_and_sample: ArchiveLocationAndSample = (
        archive_api.get_archive_location_and_sample_id_from_file_path(spring_file.as_posix())
    )
    # THEN the archive location and sample should be set to DDN and ADM1
    assert archive_location_and_sample.location == "DDN"
    assert archive_location_and_sample.sample_id == "ADM1"


def test_sort_spring_files_on_archive_location(
    archive_api: ArchiveAPI, populated_housekeeper_api: HousekeeperAPI
):
    # GIVEN a populated status_db database with two customers, one DDN and one non-DDN,
    # with the DDN customer having two samples, and the non-DDN having one sample.

    # WHEN fetching all non-archived spring files
    spring_files: List[File] = archive_api.housekeeper_api.get_all_non_archived_spring_files()
    # When sorting the returned files on the data archive locations of the customers
    sorted_spring_files: Dict[
        str, List[SampleAndFile]
    ] = archive_api.sort_spring_files_on_archive_location([file.path for file in spring_files])

    assert len(sorted_spring_files["DDN"]) == 1


def test_archive_all_non_archived_spring_files(
    archive_api: ArchiveAPI, populated_housekeeper_api: HousekeeperAPI, spring_file: Path
):
    assert False


def test_retrieve_sample():
    assert False
