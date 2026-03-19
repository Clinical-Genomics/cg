"""
Module to test the store_order_data_in_status_db method of the StoreGenericOrderService class.
The function store_order_data_in_status_db is never expected to fail, as its input order should
have always been validated before calling the function.
"""

from unittest.mock import Mock, create_autospec

from pytest_mock import MockerFixture

from cg.constants import DataDelivery, Priority, Workflow
from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import ContainerEnum, SexEnum
from cg.services.orders.lims_service.service import OrderLimsService
from cg.services.orders.storing.implementations.case_order_service import StoreCaseOrderService
from cg.services.orders.validation.order_types.balsamic.models.order import BalsamicOrder
from cg.services.orders.validation.order_types.mip_dna.models.order import MIPDNAOrder
from cg.services.orders.validation.order_types.mip_rna.models.order import MIPRNAOrder
from cg.services.orders.validation.order_types.rna_fusion.constants import RNAFusionDeliveryType
from cg.services.orders.validation.order_types.rna_fusion.models.case import RNAFusionCase
from cg.services.orders.validation.order_types.rna_fusion.models.order import RNAFusionOrder
from cg.services.orders.validation.order_types.rna_fusion.models.sample import RNAFusionSample
from cg.services.orders.validation.order_types.tomte.models.order import TomteOrder
from cg.store.models import Case, Sample
from cg.store.store import Store


def test_store_mip_order(
    store_to_submit_and_validate_orders: Store,
    mip_dna_order: MIPDNAOrder,
    store_generic_order_service: StoreCaseOrderService,
):
    # GIVEN a basic store with no samples nor cases
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert not store_to_submit_and_validate_orders.get_cases()

    # WHEN storing the order
    new_cases: list[Case] = store_generic_order_service.store_order_data_in_status_db(mip_dna_order)

    # THEN it should create and link samples and the case
    assert len(new_cases) == 2
    new_case = new_cases[0]
    assert new_case.name == "MipCase1"
    assert set(new_case.panels) == {"AID"}
    assert new_case.priority_human == Priority.priority.name

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


def test_store_mip_rna_order(
    store_to_submit_and_validate_orders: Store,
    mip_rna_order: MIPRNAOrder,
    store_generic_order_service: StoreCaseOrderService,
):
    # GIVEN a basic store with no samples nor cases
    rna_application_tag = "RNAPOAR025"
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert not store_to_submit_and_validate_orders.get_cases()
    assert store_to_submit_and_validate_orders.get_application_by_tag(tag=rna_application_tag)

    # WHEN storing a MIP-RNA order containing 1 case with 2 samples and 1 case with only 1 sample
    new_cases: list[Case] = store_generic_order_service.store_order_data_in_status_db(mip_rna_order)

    # THEN it should create and link samples and the casing
    assert len(new_cases) == 2
    first_case = new_cases[0]

    assert len(first_case.links) == 2
    new_link = first_case.links[0]
    assert first_case.data_analysis == Workflow.MIP_RNA
    assert first_case.data_delivery == str(DataDelivery.ANALYSIS_SCOUT)
    assert new_link.sample.name == "MipRNASample1"
    assert new_link.sample.application_version.application.tag == rna_application_tag


def test_store_balsamic_order(
    store_to_submit_and_validate_orders: Store,
    balsamic_order: BalsamicOrder,
    store_generic_order_service: StoreCaseOrderService,
):
    # GIVEN a Balsamic order

    # GIVEN a store with no samples nor cases
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert not store_to_submit_and_validate_orders.get_cases()

    # WHEN storing the order
    new_cases: list[Case] = store_generic_order_service.store_order_data_in_status_db(
        balsamic_order
    )

    # THEN it should create and link samples and the case
    assert len(new_cases) == 1
    new_case = new_cases[0]
    assert new_case.name == "BalsamicCase"
    assert new_case.data_analysis in [
        Workflow.BALSAMIC,
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


def test_store_rna_fusion_order(
    store_to_submit_and_validate_orders: Store,
    rnafusion_order: RNAFusionOrder,
    store_generic_order_service: StoreCaseOrderService,
):
    # GIVEN a store with no samples nor cases
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert not store_to_submit_and_validate_orders.get_cases()

    # WHEN storing a RNA Fusion order
    new_cases = store_generic_order_service.store_order_data_in_status_db(rnafusion_order)

    # THEN it should create and link samples and the casing
    assert len(new_cases) == 2
    first_case = new_cases[0]

    assert len(first_case.links) == 1
    new_link = first_case.links[0]
    assert first_case.data_analysis == Workflow.RNAFUSION
    assert first_case.data_delivery == str(DataDelivery.FASTQ_ANALYSIS)
    assert new_link.sample.name == "sample1-rna-t1"
    assert new_link.sample.application_version.application.tag == "RNAPOAR025"
    assert new_link


def test_store_tomte_order(
    store_to_submit_and_validate_orders: Store,
    tomte_order: TomteOrder,
    store_generic_order_service: StoreCaseOrderService,
):
    # GIVEN a store with no samples nor cases
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert not store_to_submit_and_validate_orders.get_cases()

    # WHEN storing a Tomte order
    new_cases = store_generic_order_service.store_order_data_in_status_db(tomte_order)

    # THEN it should create and link samples and the casing
    assert len(new_cases) == 1
    first_case = new_cases[0]

    assert len(first_case.links) == 4
    new_link = first_case.links[0]
    assert first_case.data_analysis == Workflow.TOMTE
    assert first_case.data_delivery == str(DataDelivery.FASTQ_ANALYSIS)
    assert new_link.sample.name == "sample1"
    assert new_link.sample.application_version.application.tag == "RNAPOAR025"
    assert new_link


def test_store_rnafusion_sample_is_set_to_tumour(store: Store, mocker: MockerFixture):
    # GIVEN an RNAFusion order with a new sample in it
    rna_fusion_sample = RNAFusionSample(
        application="rnafusiontag",
        container=ContainerEnum.tube,
        name="rnafusionsample",
        sex=SexEnum.female,
        source="blood",
        subject_id="rnafusion-subject",
    )
    rna_fusion_case = RNAFusionCase(name="rna-fusion-case", samples=[rna_fusion_sample])
    rna_fusion_order = RNAFusionOrder(
        cases=[rna_fusion_case],
        customer="cust000",
        project_type=OrderType.RNAFUSION,
        name="rna-fusion-order",
        delivery_type=RNAFusionDeliveryType.ANALYSIS_SCOUT,
    )

    # GIVEN that persisting to StatusDB and LIMS is successful
    mocker.patch.object(store, "commit_to_store")
    lims_service: OrderLimsService = create_autospec(OrderLimsService)
    lims_service.process_lims = Mock(
        return_value=("project_data", {rna_fusion_sample.name: "rnafusion_sample_id"})
    )

    # WHEN persisting the order data
    storing_service = StoreCaseOrderService(status_db=store, lims_service=lims_service)
    new_data: dict = storing_service.store_order(rna_fusion_order)

    # THEN the new sample is a tumour sample
    new_cases: list[Case] = new_data["records"]
    new_sample = new_cases[0].samples[0]
    assert new_sample.is_tumour
