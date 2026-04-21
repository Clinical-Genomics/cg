from unittest.mock import Mock, create_autospec

import pytest
from typed_mock import TypedMock, create_typed_mock

from cg.constants import DataDelivery
from cg.constants.lims import LimsStatus
from cg.models.orders.sample_base import ContainerEnum, PriorityEnum
from cg.services.orders.lims_service.service import OrderLimsService
from cg.services.orders.storing.implementations.microbial_fastq_order_service import (
    StoreMicrobialFastqOrderService,
)
from cg.services.orders.validation.constants import ElutionBuffer
from cg.services.orders.validation.order_types.microbial_fastq.models.order import (
    MicrobialFastqOrder,
)
from cg.services.orders.validation.order_types.microbial_fastq.models.sample import (
    MicrobialFastqSample,
)
from cg.store.models import Application, ApplicationVersion, Case, Customer, Sample
from cg.store.store import Store


def test_store_samples(
    microbial_fastq_order: MicrobialFastqOrder,
    store_microbial_fastq_order_service: StoreMicrobialFastqOrderService,
):
    # GIVEN a microbial fastq order with microbial samples

    # GIVEN a basic store with no samples and a fastq order
    store: Store = store_microbial_fastq_order_service.status_db
    assert not store._get_query(table=Sample).first()
    assert store._get_query(table=Case).count() == 0

    # WHEN storing the order
    new_samples = store_microbial_fastq_order_service.store_order_data_in_status_db(
        order=microbial_fastq_order
    )

    # THEN it should store the samples and create a case for each sample
    assert len(new_samples) == 2
    assert len(store._get_query(table=Sample).all()) == 2
    assert store._get_query(table=Case).count() == 2
    first_sample = new_samples[0]
    assert len(first_sample.links) == 1
    case_link = first_sample.links[0]
    assert case_link.case in store.get_cases()
    assert case_link.case.data_analysis
    assert case_link.case.data_delivery == DataDelivery.FASTQ

    # THEN there should be one relationship per sample which delivers it
    for sample in new_samples:
        assert len(sample.links) == 1
        assert sample.links[0].should_deliver_sample


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
    micro_fastq_sample = MicrobialFastqSample(
        application="app",
        container=ContainerEnum.tube,
        elution_buffer=ElutionBuffer.OTHER,
        priority=PriorityEnum.standard,
        name="sample",
        volume=25,
    )

    # GIVEN a store case order service
    store_order_service = StoreMicrobialFastqOrderService(
        status_db=status_db.as_type, lims_service=create_autospec(OrderLimsService)
    )

    # WHEN creating a db sample with the application
    store_order_service._create_db_sample(
        sample=micro_fastq_sample, order_name="order", customer=customer, ticket_id="1234567"
    )

    # THEN the sample should be created with LimsStatus DONE
    assert status_db.as_mock.add_sample.call_args[1]["lims_status"] == expected_lims_status
