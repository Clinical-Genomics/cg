from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.archive.archive import ArchiveAPI
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


def test_get_sample_id_from_file(
    archive_api: ArchiveAPI, populated_housekeeper_api: HousekeeperAPI, spring_file: Path
):
    sample_id: str = archive_api.get_sample_id_from_file_path(file_path=spring_file.as_posix())
    assert sample_id == "ADM1"


def test_get_archive_location_and_sample_id_from_file_path(
    archive_api: ArchiveAPI, populated_housekeeper_api: HousekeeperAPI, spring_file: Path
):
    assert False


def test_sort_spring_files_on_archive_location(
    archive_api: ArchiveAPI, populated_housekeeper_api: HousekeeperAPI, spring_file: Path
):
    assert False


def test_archive_all_non_archived_spring_files(
    archive_api: ArchiveAPI, populated_housekeeper_api: HousekeeperAPI, spring_file: Path
):
    assert False


def test_retrieve_sample():
    assert False
