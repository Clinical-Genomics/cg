from abc import abstractmethod, ABC

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.store.store import Store


class FetchDeliveryFilesService(ABC):
    """
    Abstract class that encapsulates the logic required for managing the files to deliver.
    1. Get a workflow and data delivery option
    2. Fetch the files based on tags from Housekeeper
    3. Return the files to deliver
    """

    @abstractmethod
    def __init__(self, status_db: Store, hk_api: HousekeeperAPI):
        self.status_db = status_db
        self.hk_api = hk_api

    @abstractmethod
    def get_files_to_deliver(self, case_id: str) -> list[str]:
        """Get the files to deliver."""
        pass


class FormatDeliveryFilesService(ABC):
    """
    Abstract class that encaps
    """

    @abstractmethod
    def format_files(self, case_id: str) -> None:
        """Format the files to deliver."""
        pass


class MoveDeliveryFilesService(ABC):
    """
    Abstract class that encapsulates the logic required for moving files to the customer folder. including formatting and renaming.
    """

    @abstractmethod
    def move_files(self, case_id: str) -> None:
        """Move the files to the customer folder."""
        pass


class DeliverFilesService(ABC):
    """
    Abstract class that encapsulates the logic required for delivering files to the customer.

    1. Get the files to deliver from Housekeeper based on workflow and data delivery
    2. Create a delivery folder structure in the customer folder on Hasta and move the files there
    3. Reformatting of output / renaming of files
    4. Start a Rsync job to upload the files to Caesar
    5. Track the status of the Rsync job in Trailblazer
    """

    @abstractmethod
    def __init__(
        self,
        delivery_file_manager_service: FetchDeliveryFilesService,
        move_file_service: MoveDeliveryFilesService,
    ):
        self.file_manager = delivery_file_manager_service
        self.file_mover = move_file_service

    @abstractmethod
    def deliver_files_for_case(self, case_id: str) -> None:
        """Deliver the files to the customer folder."""
        pass
