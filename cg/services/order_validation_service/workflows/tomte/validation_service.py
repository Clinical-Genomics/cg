from cg.services.order_validation_service.models.validation_error import ValidationError
from cg.services.order_validation_service.order_validation_service import OrderValidationService
from cg.services.order_validation_service.workflows.tomte.validation.field_validator import (
    TomteFieldValidator,
)
from cg.services.order_validation_service.workflows.tomte.validation.inter_field_validators import (
    each_case_contains_father,
    each_case_contains_mother,
)


tomte_validation_rules = [
    each_case_contains_mother,
    each_case_contains_father,
]


class TomteValidationService(OrderValidationService):

    def __init__(self, field_validator: TomteFieldValidator):
        self.field_validator = field_validator

    def validate(self, order_json: str) -> list[ValidationError]:
        order, field_errors = self.field_validator.validate(order_json)

        # Return early if there are basic field errors
        if field_errors:
            return field_errors

        # TODO: apply tomte validation rules to order here
