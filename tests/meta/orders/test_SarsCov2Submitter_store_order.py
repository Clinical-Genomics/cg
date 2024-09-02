import datetime as dt

from cg.constants import DataDelivery
from cg.constants.constants import Workflow
from cg.meta.orders.sars_cov_2_submitter import SarsCov2Submitter
from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import ControlEnum
from cg.models.orders.samples import SarsCov2Sample
from cg.store.models import Customer, Sample
from cg.store.store import Store


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
        customer_id=order.customer,
        data_analysis=Workflow.MUTANT,
        data_delivery=DataDelivery.FASTQ,
        order="",
        ordered=dt.datetime.now(),
        ticket_id=123456,
        items=status_data.get("samples"),
    )

    # THEN control should exist on the sample in the store
    customer: Customer = base_store.get_customer_by_internal_id(customer_internal_id=order.customer)
    sample: SarsCov2Sample
    for sample in order.samples:
        stored_sample: Sample = base_store.get_sample_by_customer_and_name(
            customer_entry_id=[customer.id], sample_name=sample.name
        )
        assert stored_sample.control == control_value
