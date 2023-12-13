from cg.meta.workflow.microsalt.quality_controller import QualityController
from cg.store.models import Application, Sample
from tests.store_helpers import StoreHelpers


def test_is_valid_total_reads_passes(quality_controller: QualityController):
    # GIVEN an application
    store = quality_controller.status_db
    application: Application = StoreHelpers.add_application(store=store, target_reads=1000)

    # GIVEN an application version
    version = StoreHelpers.add_application_version(
        store=store,
        application=application,
        prices={"standard": 1000, "priority": 2000, "express": 3000, "research": 4000},
    )

    # GIVEN a sample with a number of reads that is above the target reads
    sample: Sample = StoreHelpers.add_sample(store=store, reads=10000)

    # GIVEN that the sample is associated with the application version
    sample.application_version = version

    # WHEN controlling the quality of the sample reads
    has_valid_reads: bool = quality_controller.is_valid_total_reads(sample.internal_id)

    # THEN the sample passes the quality control
    assert has_valid_reads


def test_is_valid_total_reads_fails(quality_controller: QualityController):
    # GIVEN an application
    store = quality_controller.status_db
    application: Application = StoreHelpers.add_application(store=store, target_reads=1000)

    # GIVEN an application version
    version = StoreHelpers.add_application_version(
        store=store,
        application=application,
        prices={"standard": 1000, "priority": 2000, "express": 3000, "research": 4000},
    )

    # GIVEN a sample with a number of reads that is far below the target reads
    sample: Sample = StoreHelpers.add_sample(store=store, reads=100)

    # GIVEN that the sample is associated with the application version
    sample.application_version = version

    # WHEN controlling the quality of the sample reads
    has_valid_reads: bool = quality_controller.is_valid_total_reads(sample.internal_id)

    # THEN the sample fails the quality control
    assert not has_valid_reads
