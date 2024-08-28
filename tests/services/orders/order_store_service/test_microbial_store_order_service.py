from cg.services.orders.store_order_services.store_microbial_order import StoreMicrobialOrderService
from cg.store.models import Case
import datetime as dt
from cg.constants import DataDelivery
from cg.constants.constants import Workflow
from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import ControlEnum
from cg.models.orders.samples import SarsCov2Sample
from cg.store.models import Customer, Sample
from cg.store.store import Store


def test_microbial_samples_to_status(
    microbial_order_to_submit: dict, store_microbial_order_service: StoreMicrobialOrderService
):
    # GIVEN microbial order with three samples
    order = OrderIn.parse_obj(microbial_order_to_submit, OrderType.MICROSALT)

    # WHEN parsing for status
    data = store_microbial_order_service.order_to_status(order=order)

    # THEN it should pick out samples and relevant information
    assert len(data["samples"]) == 5
    assert data["customer"] == "cust002"
    assert data["order"] == "Microbial samples"
    assert data["comment"] == "Order comment"
    assert data["data_analysis"] == Workflow.MICROSALT
    assert data["data_delivery"] == str(DataDelivery.FASTQ)

    # THEN first sample should contain all the relevant data from the microbial order
    sample_data = data["samples"][0]
    assert sample_data["priority"] == "research"
    assert sample_data["name"] == "all-fields"
    assert sample_data.get("internal_id") is None
    assert sample_data["organism_id"] == "M.upium"
    assert sample_data["reference_genome"] == "NC_111"
    assert sample_data["application"] == "MWRNXTR003"
    assert sample_data["comment"] == "plate comment"
    assert sample_data["volume"] == "1"


def test_sarscov2_samples_to_status(
    sarscov2_order_to_submit: dict, store_microbial_order_service: StoreMicrobialOrderService
):
    # GIVEN sarscov2 order with three samples
    order = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)

    # WHEN parsing for status
    data = store_microbial_order_service.order_to_status(order=order)

    # THEN it should pick out samples and relevant information
    assert len(data["samples"]) == 6
    assert data["customer"] == "cust002"
    assert data["order"] == "Sars-CoV-2 samples"
    assert data["comment"] == "Order comment"
    assert data["data_analysis"] == Workflow.MUTANT
    assert data["data_delivery"] == str(DataDelivery.FASTQ)

    # THEN first sample should contain all the relevant data from the microbial order
    sample_data = data["samples"][0]
    assert sample_data.get("internal_id") is None
    assert sample_data["priority"] == "research"
    assert sample_data["application"] == "VWGDPTR001"
    assert sample_data["comment"] == "plate comment"
    assert sample_data["name"] == "all-fields"
    assert sample_data["organism_id"] == "SARS CoV-2"
    assert sample_data["reference_genome"] == "NC_111"
    assert sample_data["volume"] == "1"


def test_store_microbial_samples(
    base_store: Store,
    microbial_status_data: dict,
    ticket_id: str,
    store_microbial_order_service: StoreMicrobialOrderService,
):
    # GIVEN a basic store with no samples and a microbial order and one Organism
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0
    assert base_store.get_all_organisms().count() == 1

    # WHEN storing the order
    new_samples = store_microbial_order_service.store_items_in_status(
        customer_id=microbial_status_data["customer"],
        order=microbial_status_data["order"],
        ordered=dt.datetime.now(),
        ticket_id=ticket_id,
        items=microbial_status_data["samples"],
        comment="",
        data_analysis=Workflow.MICROSALT,
        data_delivery=DataDelivery.FASTQ_QC,
    )

    # THEN it should store the samples under a case (case) and the used previously unknown
    # organisms
    assert new_samples
    assert base_store._get_query(table=Case).count() == 1
    assert len(new_samples) == 5
    assert len(base_store._get_query(table=Sample).all()) == 5
    assert base_store.get_all_organisms().count() == 3


def test_store_microbial_case_data_analysis_stored(
    base_store: Store,
    microbial_status_data: dict,
    ticket_id: str,
    store_microbial_order_service: StoreMicrobialOrderService,
):
    # GIVEN a basic store with no samples and a microbial order and one Organism
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0

    # WHEN storing the order
    store_microbial_order_service.store_items_in_status(
        customer_id=microbial_status_data["customer"],
        order=microbial_status_data["order"],
        ordered=dt.datetime.now(),
        ticket_id=ticket_id,
        items=microbial_status_data["samples"],
        comment="",
        data_analysis=Workflow.MICROSALT,
        data_delivery=DataDelivery.FASTQ_QC,
    )

    # THEN store the samples under a case with the microbial data_analysis type on case level
    assert len(base_store._get_query(table=Sample).all()) > 0
    assert base_store._get_query(table=Case).count() == 1

    microbial_case = base_store.get_cases()[0]
    assert microbial_case.data_analysis == Workflow.MICROSALT
    assert microbial_case.data_delivery == str(DataDelivery.FASTQ_QC)


def test_store_microbial_sample_priority(
    base_store: Store,
    microbial_status_data: dict,
    ticket_id: str,
    store_microbial_order_service: StoreMicrobialOrderService,
):
    # GIVEN a basic store with no samples
    assert not base_store._get_query(table=Sample).first()

    # WHEN storing the order
    store_microbial_order_service.store_items_in_status(
        customer_id=microbial_status_data["customer"],
        order=microbial_status_data["order"],
        ordered=dt.datetime.now(),
        ticket_id=ticket_id,
        items=microbial_status_data["samples"],
        comment="",
        data_analysis=Workflow.MICROSALT,
        data_delivery=DataDelivery.FASTQ_QC,
    )

    # THEN it should store the sample priority
    assert len(base_store._get_query(table=Sample).all()) > 0
    microbial_sample = base_store._get_query(table=Sample).first()

    assert microbial_sample.priority_human == "research"


def test_order_to_status_control_exists(
    sarscov2_order_to_submit: dict,
    base_store: Store,
    store_microbial_order_service: StoreMicrobialOrderService,
):
    # GIVEN sarscov2 order with three samples
    order: OrderIn = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)

    # WHEN transforming order to status structure
    result: dict = store_microbial_order_service.order_to_status(order=order)

    # THEN check that control is in the result
    sample: dict
    for sample in result.get("samples"):
        assert "control" in sample


def test_order_to_status_control_has_input_value(
    sarscov2_order_to_submit: dict,
    base_store: Store,
    store_microbial_order_service: StoreMicrobialOrderService,
):
    # GIVEN sarscov2 order with three samples with control value set
    control_value = ControlEnum.positive
    order: OrderIn = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)
    sample: SarsCov2Sample
    for sample in order.samples:
        sample.control: ControlEnum = control_value

    # WHEN transforming order to status structure
    result: dict = store_microbial_order_service.order_to_status(order=order)

    # THEN check that control is in the result
    sample: dict
    for sample in result.get("samples"):
        assert control_value in sample.get("control")


def test_mutant_sample_generates_fields(sarscov2_order_to_submit: dict, base_store: Store):
    """Tests that Mutant orders with region and original_lab set can generate region_code and original_lab_address."""
    # GIVEN sarscov2 order with six samples, one without region_code and original_lab_address

    # WHEN parsing the order
    order: OrderIn = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)

    # THEN all samples should have region_code and original_lab_address set
    for sample in order.samples:
        assert sample.region_code
        assert sample.original_lab_address


def test_store_items_in_status_control_has_stored_value(
    sarscov2_order_to_submit: dict,
    base_store: Store,
    store_microbial_order_service: StoreMicrobialOrderService,
):
    # GIVEN sarscov2 order with three samples with control value
    order: OrderIn = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)
    control_value = ControlEnum.positive
    sample: SarsCov2Sample
    for sample in order.samples:
        sample.control: ControlEnum = control_value

    status_data = store_microbial_order_service.order_to_status(order=order)

    # WHEN storing the order
    store_microbial_order_service.store_items_in_status(
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
