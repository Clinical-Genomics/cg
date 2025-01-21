import pytest

from cg.services.orders.validation.model_validator.model_validator import ModelValidator
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.workflows.fluffy.models.order import FluffyOrder
from cg.services.orders.validation.workflows.rml.models.order import RmlOrder


@pytest.mark.parametrize(
    "order_fixture, expected_index_sequence, order_model",
    [
        (
            "fluffy_order_to_submit_without_index_sequence",
            "C01 IDT_10nt_568 (TGTGAGCGAA-AACTCCGATC)",
            FluffyOrder,
        ),
        ("rml_order_to_submit_without_index_sequence", "UDI 3 (CGCTGCTC-GGCAGATC)", RmlOrder),
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
    # GIVEN a pool raw order with a sample without index sequence but correct index and index number
    raw_order: dict = request.getfixturevalue(order_fixture)

    # WHEN validating the order
    order, _ = model_validator.validate(order=raw_order, model=order_model)

    # THEN the index sequence should be set to the default index sequence
    assert order.samples[0].index_sequence == expected_index_sequence
