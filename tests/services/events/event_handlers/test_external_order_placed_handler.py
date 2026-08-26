from unittest.mock import create_autospec

from cg.models.cg_config import CGConfig
from cg.services.events.event_handlers import external_order_placed_handler


def test_handle_trigger_transfer():
    # GIVEN that the order has three external samples
    # GIVEN that two of the samples are in the ExternalSample table

    # GIVEN a CGConfig
    cg_config = create_autospec(CGConfig, status_db=status_db)

    # WHEN handling the event
    external_order_placed_handler.handle()
    # THEN the transfer for the two samples in the ExternalSample table has been triggered
