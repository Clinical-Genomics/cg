import logging

from cg.exc import OrderError as OrderValidationError
from cg.models.orders.constants import OrderType
from cg.services.orders.validation.errors.case_errors import CaseError
from cg.services.orders.validation.errors.case_sample_errors import CaseSampleError
from cg.services.orders.validation.errors.order_errors import OrderError
from cg.services.orders.validation.errors.sample_errors import SampleError
from cg.services.orders.validation.errors.validation_errors import ValidationErrors
from cg.services.orders.validation.model_validator.model_validator import ModelValidator
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_type_maps import (
    ORDER_TYPE_MODEL_MAP,
    ORDER_TYPE_RULE_SET_MAP,
    RuleSet,
)
from cg.services.orders.validation.response_mapper import create_order_validation_response
from cg.services.orders.validation.utils import (
    apply_case_sample_validation,
    apply_case_validation,
    apply_order_validation,
    apply_sample_validation,
)
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class OrderValidationService:
    def __init__(self, store: Store):
        self.store = store

    def get_validation_response(self, raw_order: dict, order_type: OrderType, user_id: int) -> dict:
        model = ORDER_TYPE_MODEL_MAP[order_type]
        rule_set = ORDER_TYPE_RULE_SET_MAP[order_type]
        errors: ValidationErrors = self._get_errors(
            raw_order=raw_order, model=model, rule_set=rule_set, user_id=user_id
        )
        return create_order_validation_response(raw_order=raw_order, errors=errors)

    def parse_and_validate(self, raw_order: dict, order_type: OrderType, user_id: int) -> Order:
        model = ORDER_TYPE_MODEL_MAP[order_type]
        rule_set = ORDER_TYPE_RULE_SET_MAP[order_type]
        parsed_order, errors = ModelValidator.validate(order=raw_order, model=model)
        if parsed_order:
            parsed_order._user_id = user_id
            errors: ValidationErrors = self._get_rule_validation_errors(
                order=parsed_order,
                rule_set=rule_set,
            )
        if not errors.is_empty:
            LOG.error(errors.get_error_message())
            raise OrderValidationError(message="Order contained errors")
        return parsed_order

    def _get_errors(
        self, raw_order: dict, model: type[Order], rule_set: RuleSet, user_id: int
    ) -> ValidationErrors:
        parsed_order, errors = ModelValidator.validate(order=raw_order, model=model)
        if parsed_order:
            parsed_order._user_id = user_id
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
