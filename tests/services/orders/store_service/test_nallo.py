from unittest import mock

import pytest
from pytest_mock import MockerFixture

from cg.apps.lims import LimsAPI
from cg.constants import Workflow
from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import ContainerEnum, SexEnum, StatusEnum
from cg.services.orders.storing.implementations.case_order_service import StoreCaseOrderService
from cg.services.orders.validation.order_types.nallo.constants import NalloDeliveryType
from cg.services.orders.validation.order_types.nallo.models.case import NalloCase
from cg.services.orders.validation.order_types.nallo.models.order import NalloOrder
from cg.services.orders.validation.order_types.nallo.models.sample import NalloSample
from cg.store.models import Order
from tests.mocks.limsmock import MockLimsAPI


@pytest.fixture(autouse=True)
def mock_file_creation(nallo_order: NalloOrder):
    """Mocks LimsAPI with the correct sample data before each test in the module."""
    sample_names: list[str] = [sample.name for _, _, sample in nallo_order.enumerated_new_samples]
    name_to_id_map: dict = {
        sample_name: f"{sample_name}_internal_id" for sample_name in sample_names
    }
    with (
        mock.patch.object(LimsAPI, "submit_project", return_value={"id": 1}),
        mock.patch.object(LimsAPI, "get_samples", return_value=name_to_id_map),
    ):
        yield


def test_nallo_storing_service_success(
    nallo_order: NalloOrder, store_generic_order_service: StoreCaseOrderService
):
    # GIVEN a valid Nallo order

    # WHEN storing the order
    store_generic_order_service.store_order(nallo_order)

    # THEN the data should have been persisted
    order: Order | None = store_generic_order_service.status_db.get_order_by_ticket_id(
        nallo_order._generated_ticket_id
    )
    assert order
    assert order.workflow == Workflow.NALLO
    case_names = [case.name for case in nallo_order.cases]
    assert case_names == [case.name for case in order.cases]
    sample_names = [sample.name for _, _, sample in nallo_order.enumerated_new_samples]
    assert sample_names == [sample.name for case in order.cases for sample in case.samples]


def test_source_over_ride(
    store_generic_order_service: StoreCaseOrderService, mocker: MockerFixture
):
    # GIVEN a Nallo order with one of the samples having "other" as source
    lims_submit = mocker.patch.object(MockLimsAPI, "submit_project")
    mocker.patch.object(LimsAPI, "get_samples")
    mocker.patch.object(store_generic_order_service.status_db, "commit_to_store")
    sample = NalloSample(  # pyright: ignore [reportCallIssue]
        application="LWPBELB070",
        container=ContainerEnum.tube,
        name="nallo-sample",
        sex=SexEnum.female,
        source="other",
        source_comment="This is my other source",
        status=StatusEnum.affected,
        subject_id="subject1",
        volume=54,
    )
    case = NalloCase(name="nallo-case", panels=["OMIM-AUTO"], samples=[sample])
    order = NalloOrder(
        cases=[case],
        customer="cust000",
        delivery_type=NalloDeliveryType.ANALYSIS,
        name="nallo-order",
        project_type=OrderType.NALLO,
    )
    # WHEN storing the order
    store_generic_order_service.store_order(order)

    # THEN the sample with source "other" should have used the source_comment field
    lims_submit.assert_called_once_with(
        "None",
        [
            {
                "container": ContainerEnum.tube,
                "container_name": sample.name,
                "index_sequence": None,
                "name": sample.name,
                "udfs": {
                    "application": sample.application,
                    "capture_kit": None,
                    "collection_date": None,
                    "comment": None,
                    "concentration": None,
                    "concentration_ng_ul": None,
                    "concentration_sample": None,
                    "control": None,
                    "customer": order.customer,
                    "data_analysis": order.order_type,
                    "data_delivery": order.delivery_type,
                    "elution_buffer": None,
                    "extraction_method": None,
                    "family_name": case.name,
                    "formalin_fixation_time": None,
                    "index": None,
                    "index_number": None,
                    "lab_code": None,
                    "organism": None,
                    "organism_other": None,
                    "original_lab": None,
                    "original_lab_address": None,
                    "pool": None,
                    "post_formalin_fixation_time": None,
                    "pre_processing_method": None,
                    "primer": None,
                    "priority": "standard",
                    "quantity": None,
                    "reference_genome": None,
                    "region": None,
                    "region_code": None,
                    "require_qc_ok": False,
                    "rml_plate_name": None,
                    "selection_criteria": None,
                    "sex": "F",
                    "skip_reception_control": None,
                    "source": sample.source_comment,  # This is what the essence of the test asserts
                    "tissue_block_size": None,
                    "tumour": False,
                    "tumour_purity": None,
                    "verified_organism": None,
                    "volume": str(sample.volume),
                    "well_position_rml": None,
                },
                "well_position": None,
            }
        ],
    )
