from cg.exc import OrderError as OrderValidationError
from cg.services.order_validation_service.errors.case_errors import CaseError
from cg.services.order_validation_service.errors.case_sample_errors import CaseSampleError
from cg.services.order_validation_service.errors.order_errors import OrderError
from cg.services.order_validation_service.errors.sample_errors import SampleError
from cg.services.order_validation_service.errors.validation_errors import ValidationErrors
from cg.services.order_validation_service.model_validator.model_validator import ModelValidator
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.order_type_maps import RuleSet
from cg.services.order_validation_service.response_mapper import create_order_validation_response
from cg.services.order_validation_service.utils import (
    apply_case_sample_validation,
    apply_case_validation,
    apply_order_validation,
    apply_sample_validation,
)
from cg.store.store import Store


class OrderValidationService:
    def __init__(self, store: Store):
        self.store = store

    def get_validation_response(
        self, raw_order: dict, model: type[Order], rule_set: RuleSet
    ) -> dict:
        errors = self._get_errors(raw_order=raw_order, model=model, rule_set=rule_set)
        return create_order_validation_response(raw_order=raw_order, errors=errors)

    def _get_errors(
        self, raw_order: dict, model: type[Order], rule_set: RuleSet
    ) -> ValidationErrors:
        parsed_order, errors = ModelValidator.validate(order=raw_order, model=model)
        if parsed_order:
            errors: ValidationErrors = self._get_rule_validation_errors(
                order=parsed_order, rule_set=rule_set
            )
        return errors

    def _get_rule_validation_errors(self, order: Order, rule_set: RuleSet) -> ValidationErrors:

        case_errors = []
        case_sample_errors = []
        order_errors: list[OrderError] = apply_order_validation(
            rules=rule_set.order_rules,
            order=order,
            store=self.store,
        )
        sample_errors = []
        if isinstance(order, OrderWithCases):
            case_errors: list[CaseError] = apply_case_validation(
                rules=rule_set.case_rules,
                order=order,
                store=self.store,
            )
            case_sample_errors: list[CaseSampleError] = apply_case_sample_validation(
                rules=rule_set.case_sample_rules,
                order=order,
                store=self.store,
            )
        else:
            sample_errors: list[SampleError] = apply_sample_validation(
                rules=rule_set.sample_rules,
                order=order,
                store=self.store,
            )

        return ValidationErrors(
            case_errors=case_errors,
            case_sample_errors=case_sample_errors,
            order_errors=order_errors,
            sample_errors=sample_errors,
        )

    def parse_and_validate(self, raw_order: dict, model: type[Order], rule_set: RuleSet) -> Order:
        parsed_order, errors = ModelValidator.validate(order=raw_order, model=model)
        if parsed_order:
            errors: ValidationErrors = self._get_rule_validation_errors(
                order=parsed_order,
                rule_set=rule_set,
            )
        if not errors.is_empty:
            raise OrderValidationError(message="Order contained errors")
        return parsed_order
