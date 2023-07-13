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


def test_retrieve_sample():
    assert False
