from pydantic import AfterValidator, model_validator

from cg.constants import DataDelivery, GenePanelMasterList
from cg.models.orders.orderform_schema import OrderCase
from cg.services.order_validation_service.models.case_validators import validate_subject_id
from cg.services.order_validation_service.workflows.tomte.validators.case_validators import (
    validate_tomte_delivery_type,
)


class TomteCase(OrderCase):
    cohorts: list[str] | None = None
    data_delivery: [DataDelivery, AfterValidator(validate_tomte_delivery_type)]
    panels: list[GenePanelMasterList]
    synopsis: str | None = None

    _subject_id_validation = model_validator(mode="after")(validate_subject_id)
