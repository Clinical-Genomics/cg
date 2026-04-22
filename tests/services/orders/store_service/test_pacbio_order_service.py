from unittest.mock import Mock, create_autospec

import pytest

from cg.constants import DataDelivery, Workflow
from cg.constants.lims import LimsStatus
from cg.models.orders.sample_base import ContainerEnum, PriorityEnum, SexEnum
from cg.services.orders.lims_service.service import OrderLimsService
from cg.services.orders.storing.implementations.pacbio_order_service import StorePacBioOrderService
from cg.services.orders.validation.order_types.pacbio_long_read.models.order import PacbioOrder
from cg.services.orders.validation.order_types.pacbio_long_read.models.sample import PacbioSample
from cg.store.models import Application, ApplicationVersion, Case, Customer, Order, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_store_pacbio_order_data_in_status_db(
    store_to_submit_and_validate_orders: Store,
    pacbio_order: PacbioOrder,
    store_pacbio_order_service: StorePacBioOrderService,
):
    """Test that a PacBio order is stored in the database."""
    # GIVEN a valid Pacbio order and a Pacbio store service

    # GIVEN a basic store with no samples, cases and only a MAF order
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert store_to_submit_and_validate_orders._get_query(table=Case).count() == 0
    assert store_to_submit_and_validate_orders._get_query(table=Order).count() == 1

    # WHEN storing the order
    new_samples: list[Sample] = store_pacbio_order_service.store_order_data_in_status_db(
        order=pacbio_order
    )

    # THEN it should store the order
    assert store_to_submit_and_validate_orders._get_query(table=Order).count() == 2

    # THEN it should store the samples and create a case for each sample
    assert len(new_samples) == 3
    assert len(store_to_submit_and_validate_orders._get_query(table=Sample).all()) == 3
    assert store_to_submit_and_validate_orders._get_query(table=Case).count() == 3
    for new_sample in new_samples:
        # THEN the sample sex should be stored
        assert new_sample.sex == SexEnum.male
        # THEN the sample should have a relationship with a case
        assert len(new_sample.links) == 1
        case_sample = new_sample.links[0]
        assert case_sample.case in store_to_submit_and_validate_orders.get_cases()
        # THEN the analysis for the case should be RAW_DATA
        assert case_sample.case.data_analysis == Workflow.RAW_DATA
        # THEN the delivery type for the case should be BAM or NO_DELIVERY
        assert case_sample.case.data_delivery in [DataDelivery.BAM, DataDelivery.NO_DELIVERY]
        # THEN the case-sample should deliver the sample
        assert case_sample.should_deliver_sample


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
    fastq_sample = PacbioSample(
        application="app",
        container=ContainerEnum.tube,
        priority=PriorityEnum.standard,
        name="sample",
        sex=SexEnum.female,
        source="blood",
    )

    # GIVEN a store case order service
    store_order_service = StorePacBioOrderService(
        status_db=status_db.as_type, lims_service=create_autospec(OrderLimsService)
    )

    # WHEN creating a db sample with the application
    store_order_service._create_db_sample(
        sample=fastq_sample, order_name="order", customer=customer, ticket_id="1234567"
    )

    # THEN the sample should be created with LimsStatus DONE
    assert status_db.as_mock.add_sample.call_args[1]["lims_status"] == expected_lims_status
