from cg.services.order_validation_service.models.errors import (
    CaseError,
    CaseSampleError,
    OrderError,
    ValidationErrors,
)
from cg.services.order_validation_service.order_validation_service import (
    OrderValidationService,
)
from cg.services.order_validation_service.utils import (
    apply_case_sample_validation,
    apply_case_validation,
    apply_order_validation,
)
from cg.services.order_validation_service.workflows.tomte.validation.field.tomte_model_validator import (
    TomteModelValidator,
)
from cg.services.order_validation_service.workflows.tomte.validation_rules import (
    TOMTE_CASE_RULES,
    TOMTE_CASE_SAMPLE_RULES,
    TOMTE_ORDER_RULES,
)
from cg.store.store import Store


class TomteValidationService(OrderValidationService):

    def __init__(self, store: Store, model_validator: TomteModelValidator):
        self.store = store
        self.model_validator = model_validator

    def validate(self, raw_order: dict) -> ValidationErrors:
        order, field_errors = self.model_validator.validate(raw_order)

        if field_errors:
            return field_errors

        order_errors: list[OrderError] = apply_order_validation(
            rules=TOMTE_ORDER_RULES, order=order, store=self.store
        )
        case_errors: list[CaseError] = apply_case_validation(
            rules=TOMTE_CASE_RULES, order=order, store=self.store
        )
        case_sample_errors: list[CaseSampleError] = apply_case_sample_validation(
            rules=TOMTE_CASE_SAMPLE_RULES, order=order, store=self.store
        )

        return ValidationErrors(
            case_errors=case_errors,
            case_sample_errors=case_sample_errors,
            order_errors=order_errors,
        )
