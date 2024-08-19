from cg.services.order_validation_service.models.errors import (
    CaseError,
    OrderError,
    ValidationErrors,
)
from cg.services.order_validation_service.order_validation_service import OrderValidationService
from cg.services.order_validation_service.utils import apply_case_validation, apply_order_validation
from cg.services.order_validation_service.workflows.microsalt.validation_rules import (
    ORDER_RULES,
    SAMPLE_RULES,
)
from cg.store.store import Store


class MicroSaltValidationService(OrderValidationService):

    def __init__(self, store: Store, model_validator: MicroSaltModelValidator):
        self.store = store
        self.model_validator = model_validator

    def validate(self, raw_order: dict) -> ValidationErrors:
        order, field_errors = self.model_validator.validate(raw_order)

        if field_errors:
            return field_errors

        order_errors: list[OrderError] = apply_order_validation(
            rules=ORDER_RULES,
            order=order,
            store=self.store,
        )
        sample_errors: list[CaseError] = apply_case_validation(
            rules=SAMPLE_RULES,
            order=order,
            store=self.store,
        )

        return ValidationErrors(
            order_errors=order_errors,
            sample_errors=sample_errors,
        )
