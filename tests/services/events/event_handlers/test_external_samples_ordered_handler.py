from unittest.mock import create_autospec

from pytest_mock import MockerFixture

from cg.models.cg_config import CGConfig
from cg.services.events.event_handlers import external_samples_ordered_handler
from cg.services.events.event_handlers.external_samples_ordered_handler import (
    transfer_to_cluster_service,
)
from cg.store.models import ExternalSample, Sample
from cg.store.store import Store


def test_handle_trigger_transfer_only_for_stored_sample(mocker: MockerFixture):

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
    sample.name = "sample-name-1"
    status_db.get_sample_by_customer_and_name = lambda customer_entry_id, sample_name: (
        sample if sample_name == "sample-name-1" else create_autospec(Sample)
    )

    # GIVEN a CGConfig
    cg_config = create_autospec(CGConfig, status_db=status_db)

    # GIVEN a transfer servicer
    transfer_sample_mock = mocker.patch.object(transfer_to_cluster_service, "transfer_sample")

    # WHEN handling the event
    external_samples_ordered_handler.handle(config=cg_config, event_payload=event_payload)

    # THEN the transfer for the sample in the ExternalSample table has been triggered once
    transfer_sample_mock.assert_called_once_with(cg_config=cg_config, sample=sample)
    assert transfer_sample_mock.call_count == 1
