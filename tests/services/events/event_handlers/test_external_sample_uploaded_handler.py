from datetime import datetime
from unittest.mock import Mock, create_autospec

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

from cg.models.cg_config import CGConfig
from cg.services.events.event_handlers import external_sample_uploaded_handler
from cg.services.events.event_handlers.external_sample_uploaded_handler import (
    transfer_to_cluster_service,
)
from cg.store.models import Customer, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_handle_triggers_transfer(mocker: MockerFixture):
    # GIVEN a store with a customer
    status_db: TypedMock[Store] = create_typed_mock(Store)
    status_db.as_type.get_customer_by_internal_id_strict = Mock(
        return_value=create_autospec(Customer, internal_id="cust000", id=1)
    )
    # GIVEN a CGConfig
    cg_config: CGConfig = create_autospec(
        CGConfig,
        status_db=status_db.as_type,
    )

    # GIVEN some data
    data = {
        "customer": "cust000",  # TODO rename to cg.customer, same for others
        "sample_name": "sample-name",  # TODO rename to cg.sample, same for others
        "customer_uploaded_at": "2026-06-02T11:14:52",
    }

    # GIVEN that the sample should be transferred
    sample = create_autospec(Sample)
    status_db.as_type.get_sample_by_customer_and_name = Mock(return_value=sample)

    # GIVEN a transfer servicer
    transfer_sample_mock = mocker.patch.object(transfer_to_cluster_service, "transfer_sample")

    # WHEN calling handle with a CGConfig and some data
    external_sample_uploaded_handler.handle(config=cg_config, data=data)

    # THEN the provided data should have been added to the database
    status_db.as_mock.add_external_sample.assert_called_once_with(
        customer_id=1,
        sample_name="sample-name",
        customer_uploaded_at=datetime(
            year=2026,
            month=6,
            day=2,
            hour=11,
            minute=14,
            second=52,
        ),
    )

    # THEN the sample should be transferred
    transfer_sample_mock.assert_called_once_with(cg_config=cg_config, sample=sample)


def test_handle_not_trigger_transfer(mocker: MockerFixture):
    # GIVEN a store with a customer
    status_db: TypedMock[Store] = create_typed_mock(Store)
    status_db.as_type.get_customer_by_internal_id_strict = Mock(
        return_value=create_autospec(Customer, internal_id="cust000", id=1)
    )
    # GIVEN a CGConfig
    cg_config: CGConfig = create_autospec(CGConfig, status_db=status_db.as_type)

    # GIVEN some data
    data = {
        "customer": "cust000",
        "sample_name": "sample-name",
        "customer_uploaded_at": "2026-06-02T11:14:52",
    }

    # GIVEN that the sample should NOT be transferred
    status_db.as_type.get_sample_by_customer_and_name = Mock(return_value=None)

    # GIVEN a transfer servicer
    transfer_sample_spy = mocker.spy(transfer_to_cluster_service, "transfer_sample")

    # WHEN calling handle with a CGConfig and some data
    external_sample_uploaded_handler.handle(config=cg_config, data=data)

    # THEN the provided data should have been added to the database
    status_db.as_mock.add_external_sample.assert_called_once_with(
        customer_id=1,
        sample_name="sample-name",
        customer_uploaded_at=datetime(year=2026, month=6, day=2, hour=11, minute=14, second=52),
    )

    # THEN sample is not transferred
    transfer_sample_spy.assert_not_called()


def test_handle_invalid_sample_name():

    # GIVEN a CGConfig
    cg_config: CGConfig = create_autospec(CGConfig)

    # GIVEN some data where the sample name contains illegal letters
    data = {
        "customer": "cust000",
        "sample_name": "invalid_sample_name",
        "customer_uploaded_at": "2026-06-02T11:14:52",
    }

    # WHEN calling handle with a CGConfig and some data
    # THEN a ValidationError should be raised
    with pytest.raises(ValidationError):
        external_sample_uploaded_handler.handle(config=cg_config, data=data)


def test_handle_invalid_date_format():
    # GIVEN a CGConfig
    cg_config: CGConfig = create_autospec(CGConfig)

    # GIVEN some data where the uploaded at is malformed
    data = {
        "customer": "cust000",
        "sample_name": "sample-name",
        "customer_uploaded_at": "2026-06-02T11:14.52",
    }

    # WHEN calling handle with a CGConfig and some data
    # THEN a ValidationError should be raised
    with pytest.raises(ValidationError):
        external_sample_uploaded_handler.handle(config=cg_config, data=data)
