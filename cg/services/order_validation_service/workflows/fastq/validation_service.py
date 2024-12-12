from cg.exc import OrderError, OrderFormError
from cg.services.order_validation_service.errors.sample_errors import SampleError
from cg.services.order_validation_service.errors.validation_errors import ValidationErrors
from cg.services.order_validation_service.model_validator.model_validator import ModelValidator
from cg.services.order_validation_service.order_validation_service import OrderValidationService
from cg.services.order_validation_service.response_mapper import create_order_validation_response
from cg.services.order_validation_service.utils import (
    apply_order_validation,
    apply_sample_validation,
)
from cg.services.order_validation_service.workflows.fastq.models.order import FastqOrder
from cg.services.order_validation_service.workflows.fastq.validation_rules import SAMPLE_RULES
from cg.services.order_validation_service.workflows.order_validation_rules import ORDER_RULES
from cg.store.store import Store


class FastqValidationService(OrderValidationService):

    def __init__(self, store: Store):
        self.store = store

    def validate(self, raw_order: dict) -> dict:
        parsed_order, errors = ModelValidator.validate(order=raw_order, model=FastqOrder)
        if parsed_order:
            errors: ValidationErrors = self._perform_rule_validation(order=parsed_order)
        return create_order_validation_response(raw_order=raw_order, errors=errors)

    def _perform_rule_validation(self, order: FastqOrder) -> ValidationErrors:

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
            sample_errors=sample_errors,
            order_errors=order_errors,
        )

    def parse_and_validate(self, raw_order: dict) -> FastqOrder:
        parsed_order, errors = ModelValidator.validate(order=raw_order, model=FastqOrder)
        if parsed_order:
            errors: ValidationErrors = self._perform_rule_validation(order=parsed_order)
        if not errors.is_empty:
            raise OrderFormError(message="Order form contained errors")
        return parsed_order
