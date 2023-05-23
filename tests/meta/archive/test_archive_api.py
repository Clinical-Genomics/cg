from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.archive.archive import ArchiveAPI


def test_archive_samples(
    archive_api: ArchiveAPI, populated_housekeeper_api: HousekeeperAPI, sample_id: str
):
    # GIVEN a list of sample ids whit housekeeper bundles and SPRING files

    # WHEN archiving these samples
    archive_api.archive_samples(sample_ids=[sample_id])
    # THEN tha archive objects should be added to housekeeper along with a task_id

    assert (
        populated_housekeeper_api.files(
            bundle=sample_id, tags=[SequencingFileTag.SPRING, sample_id]
        )
        .first()
        .archive
    )


def test_retrieve_sample():
    assert False
