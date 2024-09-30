from cg.constants import PrepCategory
from cg.models.orders.sample_base import SexEnum
from cg.services.order_validation_service.workflows.balsamic.models.sample import (
    BalsamicSample,
)
from cg.store.models import Application
from cg.store.store import Store


def has_sex_and_subject(sample: BalsamicSample) -> bool:
    return bool(sample.subject_id and sample.sex != SexEnum.unknown)


def is_sample_missing_capture_kit(sample: BalsamicSample, store: Store) -> bool:
    application: Application = store.get_application_by_tag(sample.application)
    return (
        application.prep_category == PrepCategory.TARGETED_GENOME_SEQUENCING
        and not sample.capture_kit
    )