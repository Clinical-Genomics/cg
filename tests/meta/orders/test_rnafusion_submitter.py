import pytest

from cg.exc import OrderError
from cg.meta.orders.rnafusion_submitter import RnafusionSubmitter
from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn
from cg.store.store import Store


def test__validate_one_sample_per_case_multiple_samples(
    base_store: Store,
    rnafusion_order_to_submit: dict,
):
    """Tests the validation of an RNAFUSION order where two samples have the same family_name."""
    ### GIVEN an RNAFUSION order where the first and last sample share the same case
    order_data = OrderIn.parse_obj(obj=rnafusion_order_to_submit, project=OrderType.RNAFUSION)
    order_data.samples[-1].family_name = order_data.samples[0].family_name
    rnafusion_submitter = RnafusionSubmitter(status=base_store, lims=None)

    ### WHEN validating that each case has only one sample
    ### THEN an OrderError should be raised

    with pytest.raises(OrderError):
        rnafusion_submitter._validate_only_one_sample_per_case(order_data.samples)


def test__validate_one_sample_per_case_unique_samples(
    base_store: Store,
    rnafusion_order_to_submit: dict,
):
    """Tests the validation of an RNAFUSION order where all samples have unique family_name."""
    ### GIVEN an RNAFUSION order with unique family names
    order_data: OrderIn = OrderIn.parse_obj(
        obj=rnafusion_order_to_submit, project=OrderType.RNAFUSION
    )
    rnafusion_submitter: RnafusionSubmitter = RnafusionSubmitter(status=base_store, lims=None)

    ### WHEN validating that each case has only one sample
    rnafusion_submitter._validate_only_one_sample_per_case(order_data.samples)

    ### THEN no errors should be raised
