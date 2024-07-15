from cg.services.order_validation_service.models.validation_error import ValidationErrors
from cg.services.order_validation_service.order_validation_service import OrderValidationService
from cg.services.order_validation_service.utils import apply_validation
from cg.services.order_validation_service.workflows.tomte.validation.field_validator import (
    TomteFieldValidator,
)
from cg.services.order_validation_service.workflows.tomte.validation_rules import (
    TOMTE_VALIDATION_RULES,
)
from cg.store.store import Store


class TomteValidationService(OrderValidationService):

    def __init__(self, field_validator: TomteFieldValidator, store: Store):
        self.field_validator = field_validator
        self.store = store

    def validate(self, order_json: str) -> ValidationErrors:
        order, field_errors = self.field_validator.validate(order_json)

        if field_errors:
            return field_errors

        return apply_validation(rules=TOMTE_VALIDATION_RULES, order=order, store=self.store)
