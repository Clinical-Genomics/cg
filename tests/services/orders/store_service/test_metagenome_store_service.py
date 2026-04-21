"""
Module to test the store_order_data_in_status_db method of the StoreMetagenomeOrderService class.
The function store_order_data_in_status_db is never expected to fail, as its input order should
have always been validated before calling the function.
"""

from unittest.mock import Mock, create_autospec

import pytest
from typed_mock import TypedMock, create_typed_mock

from cg.constants.lims import LimsStatus
from cg.models.orders.sample_base import ContainerEnum, PriorityEnum
from cg.services.orders.lims_service.service import OrderLimsService
from cg.services.orders.storing.implementations.metagenome_order_service import (
    StoreMetagenomeOrderService,
)
from cg.services.orders.validation.constants import ElutionBuffer
from cg.services.orders.validation.order_types.metagenome.models.order import MetagenomeOrder
from cg.services.orders.validation.order_types.metagenome.models.sample import MetagenomeSample
from cg.store.models import Application, ApplicationVersion, Case, Customer, Sample
from cg.store.store import Store


def test_store_metagenome_order_data_in_status_db(
    metagenome_order: MetagenomeOrder,
    store_metagenome_order_service: StoreMetagenomeOrderService,
    store_to_submit_and_validate_orders: Store,
    ticket_id_as_int: int,
):
    # GIVEN a metagenome order

    # GIVEN a store with no samples nor cases
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert not store_to_submit_and_validate_orders.get_cases()

    # WHEN storing the order
    new_samples: list[Sample] = store_metagenome_order_service.store_order_data_in_status_db(
        metagenome_order
    )

    # THEN the samples should have been stored
    db_samples: list[Sample] = store_to_submit_and_validate_orders._get_query(table=Sample).all()
    assert set(new_samples) == set(db_samples)

    # THEN the samples should have the correct application tag
    for sample in db_samples:
        assert sample.application_version.application.tag in ["METWPFR030", "METPCFR030"]

    # THEN there should be a case for each sample
    db_cases: list[Case] = store_to_submit_and_validate_orders._get_query(table=Case).all()
    assert len(db_samples) == len(db_cases)

    # THEN each case should deliver its sample
    for sample in db_samples:
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
    metagenomics_sample = MetagenomeSample(
        application="app",
        container=ContainerEnum.tube,
        elution_buffer=ElutionBuffer.OTHER,
        priority=PriorityEnum.standard,
        name="sample",
        source="blood",
    )

    # GIVEN a Metagenomics order
    metagenomics_order: MetagenomeOrder = create_autospec(
        MetagenomeOrder, _generated_ticket_id=1234567
    )
    metagenomics_order.name = "order"

    # GIVEN a store case order service
    store_order_service = StoreMetagenomeOrderService(
        status_db=status_db.as_type, lims_service=create_autospec(OrderLimsService)
    )

    # WHEN creating a db sample with the application
    store_order_service._create_db_sample(
        sample=metagenomics_sample,
        order=metagenomics_order,
        customer=customer,
    )

    # THEN the sample should be created with LimsStatus DONE
    assert status_db.as_mock.add_sample.call_args[1]["lims_status"] == expected_lims_status
