from cg.services.order_validation_service.models.errors import (
    CaseSampleError,
    OrderError,
    ValidationErrors,
)
from cg.services.order_validation_service.order_validation_service import (
    OrderValidationService,
)
from cg.services.order_validation_service.utils import (
    apply_case_sample_validation,
    apply_order_validation,
)
from cg.services.order_validation_service.workflows.tomte.validation.field.model_validator import (
    TomteModelValidator,
)
from cg.services.order_validation_service.workflows.tomte.validation_rules import (
    TOMTE_CASE_SAMPLE_RULES,
    TOMTE_ORDER_RULES,
)
from cg.store.store import Store


class TomteValidationService(OrderValidationService):

    def __init__(self, field_validator: TomteModelValidator, store: Store):
        self.field_validator = field_validator
        self.store = store

    def validate(self, order_json: str) -> ValidationErrors:
        order, field_errors = self.field_validator.validate(order_json)

        if field_errors:
            return field_errors

        order_errors: list[OrderError] = apply_order_validation(
            rules=TOMTE_ORDER_RULES, order=order, store=self.store
        )
        case_sample_errors: list[CaseSampleError] = apply_case_sample_validation(
            rules=TOMTE_CASE_SAMPLE_RULES, order=order, store=self.store
        )

        return ValidationErrors(
            order_errors=order_errors,
            case_sample_errors=case_sample_errors,
        )
