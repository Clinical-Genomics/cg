from typing_extensions import Annotated
from pydantic import AfterValidator, Field, model_validator

from cg.constants import DataDelivery, GenePanelMasterList
from cg.constants.priority import PriorityTerms
from cg.models.orders.orderform_schema import OrderCase
from cg.models.orders.sample_base import NAME_PATTERN
from cg.services.order_validation_service.validators.case_validators import validate_subject_id
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample
from cg.services.order_validation_service.workflows.tomte.validators.case_validators import (
    validate_delivery_type,
    validate_fathers,
    validate_mothers,
)


class TomteCase(OrderCase):
    cohorts: list[str] | None = None
    data_delivery: [DataDelivery, AfterValidator(validate_delivery_type)]
    panels: list[GenePanelMasterList]
    synopsis: str | None = None

    data_delivery: DataDelivery
    internal_id: str | None = None
    name: str = Field(pattern=NAME_PATTERN, min_length=2, max_length=128)
    priority: PriorityTerms = PriorityTerms.STANDARD
    samples: Annotated[
        list[TomteSample], AfterValidator(validate_fathers), AfterValidator(validate_mothers)
    ]

    _subject_id_validation = model_validator(mode="after")(validate_subject_id)
