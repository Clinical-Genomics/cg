from cg.constants import DataDelivery
from cg.constants.constants import Workflow
from cg.models.orders.sample_base import ControlEnum
from cg.models.orders.samples import SarsCov2Sample
from cg.services.order_validation_service.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.order_validation_service.workflows.mutant.models.order import MutantOrder
from cg.services.orders.store_order_services.implementations.store_microbial_order import (
    StoreMicrobialOrderService,
)
from cg.store.models import Case, Customer, Sample
from cg.store.store import Store


def test_store_microbial_samples(
    base_store: Store,
    microsalt_order: MicrosaltOrder,
    ticket_id: str,
    store_microbial_order_service: StoreMicrobialOrderService,
):
    # GIVEN a basic store with no samples and a microbial order and one Organism
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0
    assert base_store.get_all_organisms().count() == 1

    # WHEN storing the order
    new_samples = store_microbial_order_service.store_order_data_in_status_db(microsalt_order)

    # THEN it should store the samples under a case (case) and the used previously unknown
    # organisms
    assert new_samples
    assert base_store._get_query(table=Case).count() == 1
    assert len(new_samples) == 5
    assert len(base_store._get_query(table=Sample).all()) == 5
    assert base_store.get_all_organisms().count() == 4


def test_store_microbial_case_data_analysis_stored(
    base_store: Store,
    microsalt_order: MicrosaltOrder,
    ticket_id: str,
    store_microbial_order_service: StoreMicrobialOrderService,
):
    # GIVEN a basic store with no samples and a microbial order and one Organism
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0

    # WHEN storing the order
    store_microbial_order_service.store_order_data_in_status_db(microsalt_order)

    # THEN store the samples under a case with the microbial data_analysis type on case level
    assert len(base_store._get_query(table=Sample).all()) > 0
    assert base_store._get_query(table=Case).count() == 1

    microbial_case = base_store.get_cases()[0]
    assert microbial_case.data_analysis == Workflow.MICROSALT
    assert microbial_case.data_delivery == str(DataDelivery.FASTQ_QC_ANALYSIS)


def test_store_items_in_status_control_has_stored_value(
    sarscov2_order_to_submit: dict,
    base_store: Store,
    store_microbial_order_service: StoreMicrobialOrderService,
):
    # GIVEN sarscov2 order with three samples with control value
    order = MutantOrder.model_validate(sarscov2_order_to_submit)
    order._generated_ticket_id = 123456
    control_value = ControlEnum.positive
    sample: SarsCov2Sample
    for sample in order.samples:
        sample.control = control_value

    # WHEN storing the order
    store_microbial_order_service.store_order_data_in_status_db(order)

    # THEN control should exist on the sample in the store
    customer: Customer = base_store.get_customer_by_internal_id(customer_internal_id=order.customer)
    sample: SarsCov2Sample
    for sample in order.samples:
        stored_sample: Sample = base_store.get_sample_by_customer_and_name(
            customer_entry_id=[customer.id], sample_name=sample.name
        )
        assert stored_sample.control == control_value
