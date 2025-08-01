import pytest

from cg.services.orders.validation.model_validator.model_validator import ModelValidator
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.order_types.fluffy.models.order import FluffyOrder
from cg.services.orders.validation.order_types.mutant.models.order import MutantOrder
from cg.services.orders.validation.order_types.rml.models.order import RMLOrder
from cg.services.orders.validation.order_types.rna_fusion.models.order import RNAFusionOrder
from cg.services.orders.validation.order_types.rna_fusion.models.sample import RNAFusionSample
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


def test_rnafusion_order_sets_samples_as_tumour(rnafusion_order_to_submit: dict):
    """Test that the tumour value is set to True for all samples in a RNAFUSION order."""
    # GIVEN a RNAFUSION order with samples without a specified value for tumour
    raw_samples: list[dict] = [case["samples"][0] for case in rnafusion_order_to_submit["cases"]]
    assert all(sample.get("tumour") is None for sample in raw_samples)

    # WHEN validating the order
    order, errors = ModelValidator.validate(order=rnafusion_order_to_submit, model=RNAFusionOrder)

    # THEN there should be no validation errors
    assert errors.is_empty

    # THEN the tumour value should be set to True for all parsed samples
    parsed_samples: list[RNAFusionSample] = [case.samples[0] for case in order.cases]
    assert all(sample.tumour is True for sample in parsed_samples)


def test_rnafusion_with_normal_sample_fails(rnafusion_order_to_submit: dict):
    """Test that a RNAFUSION order with a non-tumour sample fails validation."""
    # GIVEN a RNAFUSION order with a sample specified as non-tumour (normal sample)
    rnafusion_order_to_submit["cases"][0]["samples"][0]["tumour"] = False

    # WHEN validating the order
    _, errors = ModelValidator.validate(order=rnafusion_order_to_submit, model=RNAFusionOrder)

    # THEN there should be a sample validation error
    assert errors.case_sample_errors

    # THEN the error should concern the tumour field of the first sample
    assert errors.case_sample_errors[0].field == "tumour"

    # THEN the error message should indicate that a RNAFUSION order cannot contain normal samples
    assert (
        errors.case_sample_errors[0].message
        == "Value error, RNAFUSION samples must always be tumour samples"
    )


def test_set_tumour_to_false_fails_rnafusion_sample(rnafusion_order_to_submit: dict):
    """Test that setting tumour to False for a RNAFUSION sample raises an error."""
    # GIVEN a parsed RNAFUSION order
    order, _ = ModelValidator.validate(order=rnafusion_order_to_submit, model=RNAFusionOrder)

    # WHEN setting the tumour field to False for a RNAFUSION sample

    # THEN it should raise a ValueError saying that RNAFUSION samples must be tumour samples
    with pytest.raises(ValueError) as exc_info:
        order.cases[0].samples[0].tumour = False
    assert str(exc_info.value) == "RNAFUSION samples must always be tumour samples"


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
