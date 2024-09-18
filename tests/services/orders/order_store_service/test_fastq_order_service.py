import datetime as dt

import pytest

from cg.constants import DataDelivery, Workflow
from cg.constants.constants import PrepCategory
from cg.exc import OrderError
from cg.models.orders.order import OrderIn, OrderType
from cg.services.orders.store_order_services.store_fastq_order_service import StoreFastqOrderService
from cg.store.models import Application, Case, Sample
from cg.store.store import Store


def test_samples_to_status(
    fastq_order_to_submit: dict, store_fastq_order_service: StoreFastqOrderService
):
    # GIVEN fastq order with two samples
    order = OrderIn.parse_obj(fastq_order_to_submit, OrderType.FASTQ)

    # WHEN parsing for status
    data: dict = store_fastq_order_service.order_to_status(order=order)

    # THEN it should pick out samples and relevant information
    assert len(data["samples"]) == 2
    first_sample: dict = data["samples"][0]
    assert first_sample["name"] == "prov1"
    assert first_sample["application"] == "WGSPCFC060"
    assert first_sample["priority"] == "priority"
    assert first_sample["tumour"] is False
    assert first_sample["volume"] == "1"

    # THEN the other sample is a tumour
    assert data["samples"][1]["tumour"] is True


def test_store_samples(
    base_store: Store,
    fastq_status_data: dict,
    ticket_id: str,
    store_fastq_order_service: StoreFastqOrderService,
):
    # GIVEN a basic store with no samples and a fastq order
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0

    # WHEN storing the order
    new_samples = store_fastq_order_service.store_items_in_status(
        customer_id=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket_id=ticket_id,
        items=fastq_status_data["samples"],
    )

    # THEN it should store the samples and create a case for each sample
    assert len(new_samples) == 2
    assert len(base_store._get_query(table=Sample).all()) == 2
    assert base_store._get_query(table=Case).count() == 2
    first_sample = new_samples[0]
    assert len(first_sample.links) == 2
    family_link = first_sample.links[0]
    assert family_link.case in base_store.get_cases()
    assert family_link.case.data_analysis
    assert family_link.case.data_delivery in [DataDelivery.FASTQ, DataDelivery.NO_DELIVERY]


def test_store_samples_sex_stored(
    base_store: Store,
    fastq_status_data: dict,
    ticket_id: str,
    store_fastq_order_service: StoreFastqOrderService,
):
    # GIVEN a basic store with no samples and a fastq order
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0

    # WHEN storing the order
    new_samples = store_fastq_order_service.store_items_in_status(
        customer_id=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket_id=ticket_id,
        items=fastq_status_data["samples"],
    )

    # THEN the sample sex should be stored
    assert new_samples[0].sex == "male"


def test_store_fastq_samples_non_tumour_wgs_to_mip(
    base_store: Store, fastq_status_data: dict, store_fastq_order_service: StoreFastqOrderService
):
    # GIVEN a basic store with no samples and a non-tumour fastq order as wgs
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0
    base_store.get_application_by_tag(
        fastq_status_data["samples"][0]["application"]
    ).prep_category = PrepCategory.WHOLE_GENOME_SEQUENCING
    fastq_status_data["samples"][0]["tumour"] = False

    # WHEN storing the order
    new_samples = store_fastq_order_service.store_items_in_status(
        customer_id=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket_id=1234348,
        items=fastq_status_data["samples"],
    )

    # THEN the analysis for the case should be MAF
    assert new_samples[0].links[0].case.data_analysis == Workflow.MIP_DNA


def test_store_fastq_samples_tumour_wgs_to_fastq(
    base_store: Store,
    fastq_status_data: dict,
    ticket_id: str,
    store_fastq_order_service: StoreFastqOrderService,
):
    # GIVEN a basic store with no samples and a tumour fastq order as wgs
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0
    base_store.get_application_by_tag(
        fastq_status_data["samples"][0]["application"]
    ).prep_category = PrepCategory.WHOLE_GENOME_SEQUENCING
    fastq_status_data["samples"][0]["tumour"] = True

    # WHEN storing the order
    new_samples = store_fastq_order_service.store_items_in_status(
        customer_id=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket_id=ticket_id,
        items=fastq_status_data["samples"],
    )

    # THEN the analysis for the case should be RAW_DATA
    assert new_samples[0].links[0].case.data_analysis == Workflow.RAW_DATA


def test_store_fastq_samples_non_wgs_as_fastq(
    base_store: Store,
    fastq_status_data: dict,
    ticket_id: str,
    store_fastq_order_service: StoreFastqOrderService,
):
    # GIVEN a basic store with no samples and a fastq order as non wgs
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0
    non_wgs_prep_category = PrepCategory.WHOLE_EXOME_SEQUENCING

    non_wgs_applications = base_store._get_query(table=Application).filter(
        Application.prep_category == non_wgs_prep_category
    )

    assert non_wgs_applications

    for sample in fastq_status_data["samples"]:
        sample["application"] = non_wgs_applications[0].tag

    # WHEN storing the order
    new_samples = store_fastq_order_service.store_items_in_status(
        customer_id=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket_id=ticket_id,
        items=fastq_status_data["samples"],
    )

    # THEN the analysis for the case should be RAW_DATA (none)
    assert new_samples[0].links[0].case.data_analysis == Workflow.RAW_DATA


def test_store_samples_bad_apptag(
    base_store: Store,
    fastq_status_data: dict,
    ticket_id: str,
    store_fastq_order_service: StoreFastqOrderService,
):
    # GIVEN a basic store with no samples and a fastq order
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0

    # GIVEN a non-existing application tag
    for sample in fastq_status_data["samples"]:
        sample["application"] = "nonexistingtag"

    # THEN it should raise OrderError
    with pytest.raises(OrderError):
        # WHEN storing the order
        store_fastq_order_service.store_items_in_status(
            customer_id=fastq_status_data["customer"],
            order=fastq_status_data["order"],
            ordered=dt.datetime.now(),
            ticket_id=ticket_id,
            items=fastq_status_data["samples"],
        )
