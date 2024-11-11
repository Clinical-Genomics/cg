"""Module to test the StoreGenericOrderService class."""

import datetime as dt
import math
from copy import deepcopy

from cg.constants import DataDelivery, Priority, Workflow
from cg.models.orders.order import OrderIn, OrderType
from cg.services.orders.store_order_services.store_case_order import (
    StoreCaseOrderService,
)
from cg.store.models import Sample
from cg.store.store import Store


def test_cases_to_status(
    mip_order_to_submit: dict, store_generic_order_service: StoreCaseOrderService
):
    # GIVEN a scout order with a trio case
    project: OrderType = OrderType.MIP_DNA
    order = OrderIn.parse_obj(mip_order_to_submit, project=project)

    # WHEN parsing for status
    data = store_generic_order_service.order_to_status(order=order)

    # THEN it should pick out the case
    assert len(data["families"]) == 2
    family = data["families"][0]
    assert family["name"] == "family1"
    assert family["data_analysis"] == Workflow.MIP_DNA
    assert family["data_delivery"] == str(DataDelivery.SCOUT)
    assert family["priority"] == Priority.standard.name
    assert family["cohorts"] == ["Other"]
    assert (
        family["synopsis"]
        == "As for the synopsis it will be this overly complex sentence to prove that the synopsis field might in fact be a very long string, which we should be prepared for."
    )
    assert set(family["panels"]) == {"IEM"}
    assert len(family["samples"]) == 3

    first_sample = family["samples"][0]
    assert math.isclose(first_sample["age_at_sampling"], 17.18192, rel_tol=1e-09, abs_tol=1e-09)
    assert first_sample["name"] == "sample1"
    assert first_sample["application"] == "WGSPCFC030"
    assert first_sample["phenotype_groups"] == ["Phenotype-group"]
    assert first_sample["phenotype_terms"] == ["HP:0012747", "HP:0025049"]
    assert first_sample["sex"] == "female"
    assert first_sample["status"] == "affected"
    assert first_sample["subject_id"] == "subject1"
    assert first_sample["mother"] == "sample2"
    assert first_sample["father"] == "sample3"

    # ... second sample has a comment
    assert isinstance(family["samples"][1]["comment"], str)


def test_cases_to_status_synopsis(
    mip_order_to_submit: dict, store_generic_order_service: StoreCaseOrderService
):
    # GIVEN a scout order with a trio case where synopsis is None
    modified_order: dict = deepcopy(mip_order_to_submit)
    for sample in modified_order["samples"]:
        sample["synopsis"] = None

    project: OrderType = OrderType.MIP_DNA
    order = OrderIn.parse_obj(mip_order_to_submit, project=project)

    # WHEN parsing for status
    store_generic_order_service.order_to_status(order=order)

    # THEN No exception should have been raised on synopsis


def test_store_mip(
    base_store: Store,
    mip_status_data: dict,
    ticket_id: str,
    store_generic_order_service: StoreCaseOrderService,
):
    # GIVEN a basic store with no samples or nothing in it + scout order
    assert not base_store._get_query(table=Sample).first()
    assert not base_store.get_cases()

    # WHEN storing the order
    new_families = store_generic_order_service.store_items_in_status(
        customer_id=mip_status_data["customer"],
        order=mip_status_data["order"],
        ordered=dt.datetime.now(),
        ticket_id=ticket_id,
        items=mip_status_data["families"],
    )

    # THEN it should create and link samples and the case
    assert len(new_families) == 2
    new_case = new_families[0]
    assert new_case.name == "family1"
    assert set(new_case.panels) == {"IEM"}
    assert new_case.priority_human == Priority.standard.name

    assert len(new_case.links) == 3
    new_link = new_case.links[0]
    assert new_case.data_analysis == Workflow.MIP_DNA
    assert new_case.data_delivery == str(DataDelivery.SCOUT)
    assert set(new_case.cohorts) == {"Other"}
    assert (
        new_case.synopsis
        == "As for the synopsis it will be this overly complex sentence to prove that the synopsis field might in fact be a very long string, which we should be prepared for."
    )
    assert new_link.status == "affected"
    assert new_link.mother.name == "sample2"
    assert new_link.father.name == "sample3"
    assert new_link.sample.name == "sample1"
    assert new_link.sample.sex == "female"
    assert new_link.sample.application_version.application.tag == "WGSPCFC030"
    assert new_link.sample.is_tumour
    assert isinstance(new_case.links[1].sample.comment, str)

    assert set(new_link.sample.phenotype_groups) == {"Phenotype-group"}
    assert set(new_link.sample.phenotype_terms) == {"HP:0012747", "HP:0025049"}
    assert new_link.sample.subject_id == "subject1"
    assert math.isclose(new_link.sample.age_at_sampling, 17.18192, rel_tol=1e-09, abs_tol=1e-09)


def test_store_mip_rna(
    base_store: Store,
    mip_rna_status_data,
    ticket_id: str,
    store_generic_order_service: StoreCaseOrderService,
):
    # GIVEN a basic store with no samples or nothing in it + rna order
    rna_application_tag = "RNAPOAR025"
    assert not base_store._get_query(table=Sample).first()
    assert not base_store.get_cases()
    assert base_store.get_application_by_tag(tag=rna_application_tag)

    # WHEN storing the order
    new_cases = store_generic_order_service.store_items_in_status(
        customer_id=mip_rna_status_data["customer"],
        order=mip_rna_status_data["order"],
        ordered=dt.datetime.now(),
        ticket_id=ticket_id,
        items=mip_rna_status_data["families"],
    )

    # THEN it should create and link samples and the casing
    assert len(new_cases) == 1
    new_casing = new_cases[0]

    assert len(new_casing.links) == 2
    new_link = new_casing.links[0]
    assert new_casing.data_analysis == Workflow.MIP_RNA
    assert new_casing.data_delivery == str(DataDelivery.SCOUT)
    assert new_link.sample.name == "sample1-rna-t1"
    assert new_link.sample.application_version.application.tag == rna_application_tag


def test_store_cancer_samples(
    base_store: Store,
    balsamic_status_data: dict,
    ticket_id: str,
    store_generic_order_service: StoreCaseOrderService,
):

    # GIVEN a basic store with no samples and a cancer order
    assert not base_store._get_query(table=Sample).first()
    assert not base_store.get_cases()

    # WHEN storing the order
    new_families = store_generic_order_service.store_items_in_status(
        customer_id=balsamic_status_data["customer"],
        order=balsamic_status_data["order"],
        ordered=dt.datetime.now(),
        ticket_id=ticket_id,
        items=balsamic_status_data["families"],
    )

    # THEN it should create and link samples and the case
    assert len(new_families) == 1
    new_case = new_families[0]
    assert new_case.name == "family1"
    assert new_case.data_analysis in [
        Workflow.BALSAMIC,
        Workflow.BALSAMIC_QC,
        Workflow.BALSAMIC_UMI,
    ]
    assert new_case.data_delivery == str(DataDelivery.FASTQ_ANALYSIS_SCOUT)
    assert not set(new_case.panels)
    assert new_case.priority_human == Priority.standard.name

    assert len(new_case.links) == 1
    new_link = new_case.links[0]
    assert new_link.sample.name == "s1"
    assert new_link.sample.sex == "male"
    assert new_link.sample.application_version.application.tag == "WGSPCFC030"
    assert new_link.sample.comment == "other Elution buffer"
    assert new_link.sample.is_tumour
