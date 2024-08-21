from pydantic_core import ValidationError

from cg.services.order_validation_service.errors.validation_errors import ValidationErrors
from cg.services.order_validation_service.validators.field.utils import convert_errors
from cg.services.order_validation_service.workflows.mip_dna.models.order import MipDnaOrder


class MipDnaModelValidator:

    @classmethod
    def validate(cls, raw_order: dict) -> tuple[MipDnaOrder | None, ValidationErrors]:
        try:
            order = MipDnaOrder.model_validate(raw_order)
            return order, ValidationErrors()
        except ValidationError as error:
            return None, convert_errors(pydantic_errors=error)
