import logging
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class DeliveryAPI:
    """
    This class provides methods to handle the delivery process of files from the Housekeeper
    bundle to the customer's inbox.
    """

    def __init__(self, delivery_path: Path, housekeeper_api: HousekeeperAPI, store: Store):
        self.delivery_path = delivery_path
        self.housekeeper_api = housekeeper_api
        self.store = store

    def link_files_to_inbox(self) -> None:
        """Link files from Housekeeper bundle to customer's inbox."""
        raise NotImplementedError
