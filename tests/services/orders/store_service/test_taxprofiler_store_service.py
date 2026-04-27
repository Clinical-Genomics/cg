"""
Module to test the store_order_data_in_status_db method of the StoreTaxprofilerOrderService class.
The function store_order_data_in_status_db is never expected to fail, as its input order should
have always been validated before calling the function.
"""

from unittest.mock import Mock, create_autospec

import pytest

from cg.constants.lims import LimsStatus
from cg.models.orders.sample_base import ContainerEnum, PriorityEnum
from cg.services.orders.lims_service.service import OrderLimsService
from cg.services.orders.storing.implementations.taxprofiler_order_service import (
    StoreTaxprofilerOrderService,
)
from cg.services.orders.validation.constants import ElutionBuffer
from cg.services.orders.validation.order_types.taxprofiler.models.order import TaxprofilerOrder
from cg.services.orders.validation.order_types.taxprofiler.models.sample import TaxprofilerSample
from cg.store.models import Application, ApplicationVersion, Customer, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_store_taxprofiler_order_data_in_status_db(
    taxprofiler_order: TaxprofilerOrder,
    store_taxprofiler_order_service: StoreTaxprofilerOrderService,
    store_to_submit_and_validate_orders: Store,
    ticket_id_as_int: int,
):
    # GIVEN an order
    order: TaxprofilerOrder = taxprofiler_order

    # GIVEN a store with no samples nor cases
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert not store_to_submit_and_validate_orders.get_cases()

    # WHEN storing the order
    new_samples: list[Sample] = store_taxprofiler_order_service.store_order_data_in_status_db(order)

    # THEN the samples should have been stored
    db_samples: list[Sample] = store_to_submit_and_validate_orders._get_query(table=Sample).all()
    assert set(new_samples) == set(db_samples)

    # THEN the samples should have the correct application tag and should be set to deliver
    for sample in db_samples:
        assert sample.application_version.application.tag in ["METWPFR030"]
        assert len(sample.links) == 1
        assert sample.links[0].should_deliver_sample

    # THEN the order should be stored
    assert store_to_submit_and_validate_orders.get_order_by_ticket_id(ticket_id_as_int)


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
    fastq_sample = TaxprofilerSample(
        application="app",
        container=ContainerEnum.tube,
        elution_buffer=ElutionBuffer.OTHER,
        priority=PriorityEnum.standard,
        name="sample",
        source="blood",
    )

    # GIVEN a Taxprofiler order
    taxprofiler_order: TaxprofilerOrder = create_autospec(
        TaxprofilerOrder, _generated_ticket_id=1234567
    )
    taxprofiler_order.name = "order"

    # GIVEN a store case order service
    store_order_service = StoreTaxprofilerOrderService(
        status_db=status_db.as_type, lims_service=create_autospec(OrderLimsService)
    )

    # WHEN creating a db sample with the application
    store_order_service._create_db_sample(
        sample=fastq_sample, order=taxprofiler_order, customer=customer
    )

    # THEN the sample should be created with LimsStatus DONE
    assert status_db.as_mock.add_sample.call_args[1]["lims_status"] == expected_lims_status
