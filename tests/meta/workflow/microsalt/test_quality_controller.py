from pathlib import Path

from cg.meta.workflow.microsalt.constants import QUALITY_REPORT_FILE_NAME
from cg.meta.workflow.microsalt.quality_controller import MicroSALTQualityController
from cg.meta.workflow.microsalt.quality_controller.models import QualityResult
from cg.models.cg_config import CGConfig
from cg.store.models import Application, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers

PRICES = {"standard": 1_000, "priority": 2_000, "express": 3_000, "research": 4_000}


def test_is_valid_total_reads_passes(quality_controller: MicroSALTQualityController):
    # GIVEN an application
    store = quality_controller.status_db
    application: Application = StoreHelpers.add_application(store=store, target_reads=1_000)

    # GIVEN an application version
    version = StoreHelpers.add_application_version(
        store=store,
        application=application,
        prices=PRICES,
    )

    # GIVEN a sample with a number of reads that is above the target reads
    sample: Sample = StoreHelpers.add_sample(store=store, reads=10_000)

    # GIVEN that the sample is associated with the application version
    sample.application_version = version

    # WHEN controlling the quality of the sample reads
    has_valid_reads: bool = quality_controller.has_valid_total_reads(sample.internal_id)

    # THEN the sample passes the quality control
    assert has_valid_reads


def test_is_valid_total_reads_fails(quality_controller: MicroSALTQualityController):
    # GIVEN an application
    store = quality_controller.status_db
    application: Application = StoreHelpers.add_application(store=store, target_reads=1_000)

    # GIVEN an application version
    version = StoreHelpers.add_application_version(
        store=store,
        application=application,
        prices=PRICES,
    )

    # GIVEN a sample with a number of reads that is far below the target reads
    sample: Sample = StoreHelpers.add_sample(store=store, reads=100)

    # GIVEN that the sample is associated with the application version
    sample.application_version = version

    # WHEN controlling the quality of the sample reads
    has_valid_reads: bool = quality_controller.has_valid_total_reads(sample.internal_id)

    # THEN the sample fails the quality control
    assert not has_valid_reads


def test_quality_control_fails(qc_microsalt_context: CGConfig, metrics_file_failing_qc: Path):
    # GIVEN a metrics file with samples that should fail the quality control

    # GIVEN a store containing the corresponding samples
    store: Store = qc_microsalt_context.status_db

    # GIVEN a quality controller
    quality_controller = MicroSALTQualityController(store)

    # WHEN performing the quality control
    result: QualityResult = quality_controller.quality_control(metrics_file_failing_qc)

    # THEN the case should fail the quality control
    assert not result.passes_qc

    # THEN a report should be generated
    assert metrics_file_failing_qc.parent.joinpath(QUALITY_REPORT_FILE_NAME).exists()


def test_quality_control_passes(qc_microsalt_context: CGConfig, metrics_file_passing_qc: Path):
    # GIVEN a metrics file with samples that should pass the quality control

    # GIVEN a store containing the corresponding samples
    store: Store = qc_microsalt_context.status_db

    # GIVEN a quality controller
    quality_controller = MicroSALTQualityController(store)

    # WHEN performing the quality control
    result: QualityResult = quality_controller.quality_control(metrics_file_passing_qc)

    # THEN the case should pass the quality control
    assert result.passes_qc

    # THEN a report should be generated
    assert metrics_file_passing_qc.parent.joinpath(QUALITY_REPORT_FILE_NAME).exists()
