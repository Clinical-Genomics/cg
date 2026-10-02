import pytest

from cg.services.orders.validation.model_validator.model_validator import ModelValidator
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.order_types.fluffy.models.order import FluffyOrder
from cg.services.orders.validation.order_types.mutant.models.order import MutantOrder
from cg.services.orders.validation.order_types.rml.models.order import RMLOrder
from cg.services.orders.validation.order_types.tomte.models.order import TomteOrder


@pytest.mark.parametrize(
    "order_fixture, expected_index_sequence, order_model",
    [
        ("fluffy_order_to_submit", "C01 IDT_10nt_568 (TGTGAGCGAA-AACTCCGATC)", FluffyOrder),
        ("rml_order_to_submit", "C01 IDT_10nt_568 (TGTGAGCGAA-AACTCCGATC)", RMLOrder),
    ],
    ids=["fluffy", "rml"],
)
def test_validate_pool_sample_default_index(
    order_fixture: str,
    expected_index_sequence: str,
    order_model: type[Order],
    model_validator: ModelValidator,
    request: pytest.FixtureRequest,
):
    """Test the default index sequence is set for a pool sample without index sequence."""
    # GIVEN a pool raw order with a sample without index sequence but correct index and index number
    raw_order: dict = request.getfixturevalue(order_fixture)
    assert not raw_order["samples"][0]["index_sequence"]

    # WHEN validating the order
    order, _ = model_validator.validate(order=raw_order, model=order_model)

    # THEN the index sequence should be set to the default index sequence
    assert order.samples[0]._index_sequence == expected_index_sequence


def test_validate_mutant_sample_gets_lab_and_region(
    sarscov2_order_to_submit: dict, model_validator: ModelValidator
):
    """Test the lab address and region code are set for a mutant sample without these fields."""
    # GIVEN a Mutant order with a sample without lab address and region code
    assert not sarscov2_order_to_submit["samples"][0]["original_lab_address"]
    assert not sarscov2_order_to_submit["samples"][0]["region_code"]

    # WHEN validating the order
    order, _ = model_validator.validate(order=sarscov2_order_to_submit, model=MutantOrder)

    # THEN the lab address and region code should be set
    assert order.samples[0].original_lab_address == "171 76 Stockholm"
    assert order.samples[0].region_code == "01"


def test_order_field_error(valid_order: TomteOrder, model_validator: ModelValidator):
    # GIVEN a Tomte order with an order field error
    valid_order.name = ""
    raw_order: dict = valid_order.model_dump(by_alias=True)

    # WHEN validating the order
    _, errors = model_validator.validate(order=raw_order, model=TomteOrder)

    # THEN there should be an order error
    assert errors.order_errors

    # THEN the error should concern the missing name
    assert errors.order_errors[0].field == "name"


def test_case_field_error(valid_order: TomteOrder, model_validator: ModelValidator):
    # GIVEN a Tomte order with a case field error
    valid_order.cases[0].priority = None
    raw_order: dict = valid_order.model_dump()

    # WHEN validating the order
    _, errors = model_validator.validate(order=raw_order, model=TomteOrder)

    # THEN there should be a case error
    assert errors.case_errors

    # THEN the error should concern the missing name
    assert errors.case_errors[0].field == "priority"


def test_case_sample_field_error(valid_order: TomteOrder, model_validator: ModelValidator):

    # GIVEN a Tomte order with a case sample error
    valid_order.cases[0].samples[0].well_position = 1.8
    raw_order: dict = valid_order.model_dump()

    # WHEN validating the order
    _, errors = model_validator.validate(order=raw_order, model=TomteOrder)

    # THEN a case sample error should be returned
    assert errors.case_sample_errors

    # THEN the case sample error should concern the invalid data type
    assert errors.case_sample_errors[0].field == "well_position"


def test_order_case_and_case_sample_field_error(
    valid_order: TomteOrder, model_validator: ModelValidator
):
    # GIVEN a Tomte order with an order, case and case sample error
    valid_order.name = None
    valid_order.cases[0].priority = None
    valid_order.cases[0].samples[0].well_position = 1.8
    raw_order: dict = valid_order.model_dump(by_alias=True)

    # WHEN validating the order
    _, errors = model_validator.validate(order=raw_order, model=TomteOrder)

    # THEN all errors should be returned
    assert errors.order_errors
    assert errors.case_errors
    assert errors.case_sample_errors

    # THEN the errors should concern the relevant fields
    assert errors.order_errors[0].field == "name"
    assert errors.case_errors[0].field == "priority"
    assert errors.case_sample_errors[0].field == "well_position"


def test_null_conversion(valid_order: TomteOrder, model_validator: ModelValidator):
    # GIVEN a Tomte order with a sample with empty concentration
    valid_order.cases[0].samples[0].concentration_ng_ul = ""
    raw_order: dict = valid_order.model_dump(by_alias=True)

    # WHEN validating the order
    order, _ = model_validator.validate(order=raw_order, model=TomteOrder)

    # THEN the empty concentration should be converted to None
    assert order.cases[0].samples[0].concentration_ng_ul is None


def test_skip_rc_default_conversion(valid_order: TomteOrder, model_validator: ModelValidator):
    # GIVEN a Tomte order with skip_reception_control set to None
    valid_order.skip_reception_control = None
    raw_order: dict = valid_order.model_dump(by_alias=True)

    # WHEN validating the order
    order, _ = model_validator.validate(order=raw_order, model=TomteOrder)

    # THEN the skip_reception_control value should be converted to None
    assert order.skip_reception_control is False
