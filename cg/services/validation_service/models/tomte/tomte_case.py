from pydantic import model_validator

from cg.constants import GenePanelMasterList
from cg.models.orders.orderform_schema import OrderCase
from cg.services.validation_service.models.case_validators import validate_subject_id


class TomteCase(OrderCase):
    cohorts: list[str] | None = None
    panels: list[GenePanelMasterList]
    synopsis: str | None = None

    _subject_id_validation = model_validator(mode="after")(validate_subject_id)
