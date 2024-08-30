from cg.models.orders.sample_base import SexEnum
from cg.services.order_validation_service.workflows.balsamic.models.sample import (
    BalsamicSample,
)


def has_sex_and_subject(sample: BalsamicSample) -> bool:
    return bool(sample.subject_id and sample.sex != SexEnum.unknown)
