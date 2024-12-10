from cg.services.order_validation_service.errors.order_errors import OrderError
from cg.services.order_validation_service.errors.sample_errors import SampleError
from cg.services.order_validation_service.errors.validation_errors import ValidationErrors
from cg.services.order_validation_service.model_validator.model_validator import ModelValidator
from cg.services.order_validation_service.order_validation_service import OrderValidationService
from cg.services.order_validation_service.response_mapper import create_order_validation_response
from cg.services.order_validation_service.utils import (
    apply_order_validation,
    apply_sample_validation,
)
from cg.services.order_validation_service.workflows.microbial_fastq.models.order import (
    MicrobialFastqOrder,
)
from cg.services.order_validation_service.workflows.microbial_fastq.validation_rules import (
    SAMPLE_RULES,
)
from cg.services.order_validation_service.workflows.order_validation_rules import ORDER_RULES
from cg.store.store import Store


class MicrobialFastqValidationService(OrderValidationService):

    def __init__(self, store: Store):
        self.store = store

    def validate(self, raw_order: dict) -> dict:
        errors: ValidationErrors = self._get_errors(raw_order)
        return create_order_validation_response(raw_order=raw_order, errors=errors)

    def _get_errors(self, raw_order: dict) -> ValidationErrors:
        order, field_errors = ModelValidator.validate(order=raw_order, model=MicrobialFastqOrder)

        if not order:
            return field_errors

        order_errors: list[OrderError] = apply_order_validation(
            rules=ORDER_RULES,
            order=order,
            store=self.store,
        )
        sample_errors: list[SampleError] = apply_sample_validation(
            rules=SAMPLE_RULES,
            order=order,
            store=self.store,
        )

        return ValidationErrors(
            order_errors=order_errors,
            sample_errors=sample_errors,
        )
