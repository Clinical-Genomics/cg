from unittest.mock import ANY, Mock, create_autospec

from pytest_mock import MockerFixture

from cg.models.cg_config import CGConfig
from cg.services.events.event_handlers import external_samples_ordered_handler
from cg.services.events.event_handlers.external_samples_ordered_handler import (
    transfer_to_cluster_service,
)
from cg.store.models import ExternalSample, Sample
from cg.store.store import Store


def test_handle_trigger_transfer(mocker: MockerFixture):

    # GIVEN that the order has two external samples
    event_payload = {
        "status_db.customer": "cust000",
        "status_db.sample_names": ["sample-name-1", "sample-name-2"],
    }

    # GIVEN that one of the samples are in the ExternalSample table
    status_db: Store = create_autospec(Store)

    status_db.get_external_sample = lambda customer_id, sample_name: (
        create_autospec(ExternalSample) if sample_name == "sample-name-1" else None
    )
    sample: Sample = create_autospec(Sample)
    status_db.get_sample_by_customer_and_name = Mock(return_value=sample)

    # GIVEN a CGConfig
    cg_config = create_autospec(CGConfig, status_db=status_db)

    # GIVEN a transfer servicer
    transfer_sample_mock = mocker.patch.object(transfer_to_cluster_service, "transfer_sample")

    # WHEN handling the event
    external_samples_ordered_handler.handle(config=cg_config, event_payload=event_payload)

    # THEN only the sample in the ExternalSample table is fetched
    status_db.get_sample_by_customer_and_name.assert_called_once_with(
        customer_entry_id=ANY, sample_name="sample-name-1"
    )

    # THEN the transfer for the sample in the ExternalSample table has been triggered
    transfer_sample_mock.assert_called_once_with(cg_config=cg_config, sample=sample)
