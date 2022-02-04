import pytest
from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.exc import OrderError
from cg.meta.orders.sars_cov_2_submitter import SarsCov2Submitter
from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import ControlEnum
from cg.models.orders.samples import SarsCov2Sample
from cg.store import Store, models
from tests.store_helpers import StoreHelpers
import datetime as dt


def test_store_items_in_status_control_has_stored_value(
    sarscov2_order_to_submit: dict, base_store: Store
):
    # GIVEN sarscov2 order with three samples with control value
    order: OrderIn = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)
    control_value = ControlEnum.positive
    sample: SarsCov2Sample
    for sample in order.samples:
        sample.control: ControlEnum = control_value
    submitter: SarsCov2Submitter = SarsCov2Submitter(status=base_store, lims=None)
    status_data = submitter.order_to_status(order=order)

    # WHEN storing the order
    submitter.store_items_in_status(
        comment="",
        customer=order.customer,
        data_analysis=Pipeline.SARS_COV_2,
        data_delivery=DataDelivery.FASTQ,
        order="",
        ordered=dt.datetime.now(),
        ticket=123456,
        items=status_data.get("samples"),
    )

    # THEN control should exist on the sample in the store
    customer = base_store.customer(order.customer)
    sample: SarsCov2Sample
    for sample in order.samples:
        stored_sample: models.Sample = base_store.find_samples(
            customer=customer, name=sample.name
        ).first()
        assert stored_sample.control == control_value
