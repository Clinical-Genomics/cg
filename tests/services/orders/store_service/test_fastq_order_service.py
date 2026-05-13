"""
Module to test the store_order_data_in_status_db method of the StoreFastqOrderService class.
The function store_order_data_in_status_db is never expected to fail, as its input order should
have always been validated before calling the function.
"""

from unittest.mock import Mock, create_autospec

import pytest

from cg.constants import DataDelivery, Workflow
from cg.constants.lims import LimsStatus
from cg.models.orders.sample_base import ContainerEnum, PriorityEnum, SexEnum
from cg.services.orders.lims_service.service import OrderLimsService
from cg.services.orders.storing.implementations.fastq_order_service import StoreFastqOrderService
from cg.services.orders.validation.constants import ElutionBuffer
from cg.services.orders.validation.order_types.fastq.models.order import FastqOrder
from cg.services.orders.validation.order_types.fastq.models.sample import FastqSample
from cg.store.models import Application, ApplicationVersion, Case, CaseSample, Customer, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_store_order_data_in_status_db(
    store_to_submit_and_validate_orders: Store,
    store_fastq_order_service: StoreFastqOrderService,
    fastq_order: FastqOrder,
    ticket_id_as_int: int,
):
    """Test that a Fastq order with two WGS samples, one being tumour, is stored in the database."""

    # GIVEN a fastq order with two WGS samples, the first one being a tumour sample

    # GIVEN a basic store with no samples nor cases
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert store_to_submit_and_validate_orders._get_query(table=Case).count() == 0

    # WHEN storing the order
    new_samples: list[Sample] = store_fastq_order_service.store_order_data_in_status_db(fastq_order)

    # THEN it should store the order
    assert store_to_submit_and_validate_orders.get_order_by_ticket_id(ticket_id_as_int)

    # THEN it should store the samples
    db_samples: list[Sample] = store_to_submit_and_validate_orders._get_query(table=Sample).all()
    assert set(new_samples) == set(db_samples)

    # THEN it should create one case per sample
    cases: list[Case] = store_to_submit_and_validate_orders._get_query(table=Case).all()
    assert len(cases) == 2
    links: list[CaseSample] = store_to_submit_and_validate_orders._get_query(table=CaseSample).all()
    assert len(links) == 2
    assert cases[0].data_analysis == Workflow.RAW_DATA
    assert cases[1].data_analysis == Workflow.RAW_DATA

    # THEN each sample should have a raw data case that should deliver the sample
    assert cases[0].data_analysis == Workflow.RAW_DATA
    assert cases[0].links[0].should_deliver_sample
    assert cases[1].data_analysis == Workflow.RAW_DATA
    assert cases[1].links[0].should_deliver_sample

    # THEN the analysis case has allowed data deliveries
    assert cases[0].data_delivery in [DataDelivery.FASTQ, DataDelivery.NO_DELIVERY]

    # THEN the sample sex should be stored
    assert db_samples[0].sex == "male"


@pytest.mark.parametrize(
    "is_external, expected_lims_status", [(True, LimsStatus.DONE), (False, LimsStatus.PENDING)]
)
def test_create_db_sample_with_lims_status(is_external: bool, expected_lims_status: LimsStatus):
    # GIVEN a store containing an external application
    application: Application = create_autospec(Application, is_external=is_external)
    application_version: ApplicationVersion = create_autospec(
        ApplicationVersion, application=application
    )
    status_db: TypedMock[Store] = create_typed_mock(Store)
    status_db.as_type.get_current_application_version_by_tag = Mock(
        return_value=application_version
    )
    customer: Customer = create_autospec(Customer)

    # GIVEN an order sample
    fastq_sample = FastqSample(
        application="app",
        container=ContainerEnum.tube,
        elution_buffer=ElutionBuffer.OTHER,
        priority=PriorityEnum.standard,
        name="sample",
        sex=SexEnum.female,
        source="blood",
        subject_id="father",
    )

    # GIVEN a store case order service
    store_order_service = StoreFastqOrderService(
        status_db=status_db.as_type, lims_service=create_autospec(OrderLimsService)
    )

    # WHEN creating a db sample with the application
    store_order_service._create_db_sample(
        sample=fastq_sample, order_name="order", customer=customer, ticket_id="1234567"
    )

    # THEN the sample should be created with LimsStatus DONE
    assert status_db.as_mock.add_sample.call_args[1]["lims_status"] == expected_lims_status
