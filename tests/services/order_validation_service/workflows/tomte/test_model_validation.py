from cg.services.order_validation_service.model_validator.model_validator import (
    ModelValidator,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder


def test_valid_order_is_parsed(valid_order: TomteOrder):
    # GIVEN a valid order
    order = valid_order.model_dump(by_alias=True)

    # WHEN parsing the order
    order, errors = ModelValidator.validate(order=order, model=TomteOrder)

    # THEN the parsed order is returned
    assert order

    # THEN the errors are empty
    assert not errors.case_errors
    assert not errors.case_sample_errors
    assert not errors.order_errors
    assert not errors.sample_errors


def test_order_field_error(valid_order: TomteOrder):
    # GIVEN an order with an order field error
    valid_order.name = ""
    order = valid_order.model_dump(by_alias=True)

    # WHEN validating the order
    order, errors = ModelValidator.validate(order=order, model=TomteOrder)

    # THEN there should be an order error
    assert errors.order_errors

    # THEN the error should concern the missing name
    assert errors.order_errors[0].field == "name"


def test_case_field_error(valid_order: TomteOrder):
    # GIVEN an order with a case field error
    valid_order.cases[0].priority = None
    order = valid_order.model_dump()

    # WHEN validating the order
    order, errors = ModelValidator.validate(order=order, model=TomteOrder)

    # THEN there should be a case error
    assert errors.case_errors

    # THEN the error should concern the missing name
    assert errors.case_errors[0].field == "priority"


def test_case_sample_field_error(valid_order: TomteOrder):

    # GIVEN an order with a case sample error
    valid_order.cases[0].samples[0].well_position = 1.8
    order = valid_order.model_dump()

    # WHEN validating the order
    order, errors = ModelValidator.validate(order=order, model=TomteOrder)

    # THEN a case sample error should be returned
    assert errors.case_sample_errors

    # THEN the case sample error should concern the invalid data type
    assert errors.case_sample_errors[0].field == "well_position"


def test_order_case_and_case_sample_field_error(valid_order: TomteOrder):
    # GIVEN an order with an order, case and case sample error
    valid_order.name = None
    valid_order.cases[0].priority = None
    valid_order.cases[0].samples[0].well_position = 1.8
    order = valid_order.model_dump(by_alias=True)

    # WHEN validating the order
    order, errors = ModelValidator.validate(order=order, model=TomteOrder)

    # THEN all errors should be returned
    assert errors.order_errors
    assert errors.case_errors
    assert errors.case_sample_errors

    # THEN the errors should concern the relevant fields
    assert errors.order_errors[0].field == "name"
    assert errors.case_errors[0].field == "priority"
    assert errors.case_sample_errors[0].field == "well_position"


def test_null_conversion(valid_order: TomteOrder):
    # GIVEN an order with an order, case and case sample error
    valid_order.cases[0].samples[0].concentration_ng_ul = ""
    order = valid_order.model_dump(by_alias=True)

    # WHEN validating the order
    order, errors = ModelValidator.validate(order=order, model=TomteOrder)

    assert order
