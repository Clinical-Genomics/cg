from unittest.mock import create_autospec

from pytest_mock import MockerFixture

from cg.models.cg_config import CGConfig
from cg.services.events.event_handlers import external_sample_transfer_failed_handler

from cg.services.events.external_sample_transfer

def test_handle_failure_successfully(mocker: MockerFixture):
    # event, metadata
    config = create_autospec(CGConfig)

    event_payload = {}

    transfer_to_cluster_mock = mocker.patch.object(transfer_to_cluster_service, "transfer_sample")

    # start another rsync job using transfer to cluster service
    external_sample_transfer_failed_handler.handle(config=config, event_payload=)

    # THEN a new rsync job should have been sent out
    transfer_to_cluster_mock.assert_called_once_with()
