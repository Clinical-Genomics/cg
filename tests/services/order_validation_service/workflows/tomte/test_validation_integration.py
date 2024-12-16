from cg.services.order_validation_service.order_type_maps import RuleSet
from cg.services.order_validation_service.order_validation_service import OrderValidationService
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder


def test_valid_order(
    valid_order: TomteOrder,
    tomte_validation_service: OrderValidationService,
    tomte_rule_set: RuleSet,
):

    # GIVEN a valid order

    # WHEN validating the order
    errors = tomte_validation_service._get_errors(
        raw_order=valid_order.model_dump(by_alias=True), model=TomteOrder, rule_set=tomte_rule_set
    )

    # THEN no errors should be raised
    assert not errors.order_errors
    assert not errors.case_errors
    assert not errors.case_sample_errors


def test_valid_order_conversion(
    valid_order: TomteOrder,
    tomte_validation_service: OrderValidationService,
    tomte_rule_set: RuleSet,
):

    # GIVEN a valid order
    order: dict = valid_order.model_dump(by_alias=True)

    # WHEN validating the order
    response = tomte_validation_service.get_validation_response(
        raw_order=order, model=TomteOrder, rule_set=tomte_rule_set
    )

    # THEN a response should be given
    assert response


def test_order_error_conversion(
    valid_order: TomteOrder,
    tomte_validation_service: OrderValidationService,
    tomte_rule_set: RuleSet,
):

    # GIVEN an order with a missing field on order level
    valid_order.name = ""
    order: dict = valid_order.model_dump(by_alias=True)

    # WHEN validating the order
    response: dict = tomte_validation_service.get_validation_response(
        raw_order=order, model=TomteOrder, rule_set=tomte_rule_set
    )

    # THEN there should be an error for the missing name
    assert response["name"]["errors"]


def test_case_error_conversion(
    valid_order, tomte_validation_service: OrderValidationService, tomte_rule_set: RuleSet
):

    # GIVEN an order with a faulty case priority
    valid_order.cases[0].priority = "Non-existent priority"
    order = valid_order.model_dump(by_alias=True)

    # WHEN validating the order
    response: dict = tomte_validation_service.get_validation_response(
        raw_order=order, model=TomteOrder, rule_set=tomte_rule_set
    )

    # THEN there should be an error for the faulty priority
    assert response["cases"][0]["priority"]["errors"]


def test_sample_error_conversion(
    valid_order: TomteOrder,
    tomte_validation_service: OrderValidationService,
    tomte_rule_set: RuleSet,
):

    # GIVEN an order with a sample with an invalid field
    valid_order.cases[0].samples[0].volume = 1
    invalid_order: dict = valid_order.model_dump(by_alias=True)

    # WHEN validating the order
    response = tomte_validation_service.get_validation_response(
        raw_order=invalid_order, model=TomteOrder, rule_set=tomte_rule_set
    )

    # THEN an error should be returned regarding the invalid volume
    assert response["cases"][0]["samples"][0]["volume"]["errors"]
