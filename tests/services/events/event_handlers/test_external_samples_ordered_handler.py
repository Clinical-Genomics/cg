from unittest.mock import Mock, call, create_autospec

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
        "cg.customer": "cust000",
        "cg.sample_names": ["sample-name-1", "sample-name-2"],
    }

    # GIVEN that one of the samples are in the ExternalSample table
    status_db: Store = create_autospec(Store)

    def mock_get_external_sample(customer_id: int, sample_name: str):
        if sample_name == "sample-name-1":
            return create_autospec(ExternalSample)
        else:
            return None

    status_db.get_external_sample = mock_get_external_sample
    sample: Sample = create_autospec(Sample)
    status_db.get_sample_by_customer_and_name = Mock(return_value=sample)

    # GIVEN a CGConfig
    cg_config = create_autospec(CGConfig, status_db=status_db)

    # GIVEN a transfer servicer
    transfer_sample_mock = mocker.patch.object(transfer_to_cluster_service, "transfer_sample")

    # WHEN handling the event
    external_samples_ordered_handler.handle()

    # THEN the transfer for the two samples in the ExternalSample table has been triggered
    call()
