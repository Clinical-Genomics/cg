import pytest

from cg.exc import OrderError
from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn
from cg.services.orders.validate_order_services.validate_case_order import (
    ValidateCaseOrderService,
)
from cg.store.store import Store


def test__validate_one_sample_per_case_multiple_samples(
    base_store: Store,
    rnafusion_order_to_submit: dict,
):
    """Tests the validation of an RNAFUSION order where two samples have the same family_name."""
    ### GIVEN an RNAFUSION order where the first and last sample share the same case
    order_data = OrderIn.parse_obj(obj=rnafusion_order_to_submit, project=OrderType.RNAFUSION)
    order_data.samples[-1].family_name = order_data.samples[0].family_name
    validator = ValidateCaseOrderService(base_store)

    ### WHEN validating that each case has only one sample
    ### THEN an OrderError should be raised

    with pytest.raises(OrderError):
        validator._validate_only_one_sample_per_case(order_data.samples)


def test__validate_one_sample_per_case_unique_samples(
    base_store: Store,
    rnafusion_order_to_submit: dict,
):
    """Tests the validation of an RNAFUSION order where all samples have unique family_name."""
    ### GIVEN an RNAFUSION order with unique family names
    order_data: OrderIn = OrderIn.parse_obj(
        obj=rnafusion_order_to_submit, project=OrderType.RNAFUSION
    )
    validator = ValidateCaseOrderService(base_store)

    ### WHEN validating that each case has only one sample
    validator._validate_only_one_sample_per_case(order_data.samples)

    ### THEN no errors should be raised
