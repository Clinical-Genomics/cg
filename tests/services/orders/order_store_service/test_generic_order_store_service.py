"""Module to test the StoreGenericOrderService class."""

from cg.constants import DataDelivery, Priority, Workflow
from cg.services.order_validation_service.workflows.balsamic.models.order import BalsamicOrder
from cg.services.order_validation_service.workflows.mip_dna.models.order import MipDnaOrder
from cg.services.order_validation_service.workflows.mip_rna.models.order import MipRnaOrder
from cg.services.orders.store_order_services.store_case_order import StoreCaseOrderService
from cg.store.models import Sample
from cg.store.store import Store


def test_store_mip(
    mip_dna_submit_store: Store,
    mip_dna_order: MipDnaOrder,
    ticket_id: str,
    store_generic_order_service: StoreCaseOrderService,
):
    # GIVEN a basic store with no samples or nothing in it + scout order
    assert not mip_dna_submit_store._get_query(table=Sample).first()
    assert not mip_dna_submit_store.get_cases()

    # WHEN storing the order
    new_families = store_generic_order_service.store_items_in_status(mip_dna_order)

    # THEN it should create and link samples and the case
    assert len(new_families) == 2
    new_case = new_families[0]
    assert new_case.name == "MipCase1"
    assert set(new_case.panels) == {"AID"}
    assert new_case.priority_human == Priority.standard.name

    assert len(new_case.links) == 3
    new_link = new_case.links[2]
    assert new_case.data_analysis == Workflow.MIP_DNA
    assert new_case.data_delivery == str(DataDelivery.ANALYSIS_SCOUT)
    assert (
        new_case.synopsis
        == "This is a long string to test the buffer length because surely this is the best way to do this and there are no better ways of doing this."
    )
    assert new_link.status == "affected"
    assert new_link.father.name == "MipSample1"
    assert new_link.mother.name == "MipSample2"
    assert new_link.sample.name == "MipSample3"
    assert new_link.sample.sex == "female"
    assert new_link.sample.application_version.application.tag == "WGSPCFC030"
    assert isinstance(new_case.links[1].sample.comment, str)

    assert set(new_link.sample.phenotype_groups) == {"Phenotype-group"}
    assert set(new_link.sample.phenotype_terms) == {"HP:0012747", "HP:0025049"}
    assert new_link.sample.subject_id == "Subject3"


def test_store_mip_rna(
    base_store: Store,
    mip_rna_order: MipRnaOrder,
    store_generic_order_service: StoreCaseOrderService,
):
    # GIVEN a basic store with no samples or nothing in it + rna order
    rna_application_tag = "RNAPOAR025"
    assert not base_store._get_query(table=Sample).first()
    assert not base_store.get_cases()
    assert base_store.get_application_by_tag(tag=rna_application_tag)

    # WHEN storing a MIP-RNA order containing 1 case with 2 samples and 1 case with only 1 sample
    new_cases = store_generic_order_service.store_items_in_status(mip_rna_order)

    # THEN it should create and link samples and the casing
    assert len(new_cases) == 2
    first_case = new_cases[0]

    assert len(first_case.links) == 2
    new_link = first_case.links[0]
    assert first_case.data_analysis == Workflow.MIP_RNA
    assert first_case.data_delivery == str(DataDelivery.ANALYSIS_SCOUT)
    assert new_link.sample.name == "MipRNASample1"
    assert new_link.sample.application_version.application.tag == rna_application_tag


def test_store_cancer_samples(
    balsamic_submit_store: Store,
    balsamic_order: BalsamicOrder,
    ticket_id: str,
    store_generic_order_service: StoreCaseOrderService,
):

    # GIVEN a basic store with no samples and a cancer order
    assert not balsamic_submit_store._get_query(table=Sample).first()
    assert not balsamic_submit_store.get_cases()

    # WHEN storing the order
    new_families = store_generic_order_service.store_items_in_status(balsamic_order)

    # THEN it should create and link samples and the case
    assert len(new_families) == 1
    new_case = new_families[0]
    assert new_case.name == "BalsamicCase"
    assert new_case.data_analysis in [
        Workflow.BALSAMIC,
        Workflow.BALSAMIC_QC,
        Workflow.BALSAMIC_UMI,
    ]
    assert new_case.data_delivery == str(DataDelivery.ANALYSIS_SCOUT)
    assert not set(new_case.panels)
    assert new_case.priority_human == Priority.standard.name

    assert len(new_case.links) == 1
    new_link = new_case.links[0]
    assert new_link.sample.name == "BalsamicSample"
    assert new_link.sample.sex == "male"
    assert new_link.sample.application_version.application.tag == "PANKTTR100"
    assert new_link.sample.comment == "This is a sample comment"
    assert new_link.sample.is_tumour
