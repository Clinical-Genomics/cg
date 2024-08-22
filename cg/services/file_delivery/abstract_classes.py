from abc import abstractmethod, ABC

from cg.services.file_delivery.fetch_file_service.fetch_delivery_files_service import (
    FetchDeliveryFilesService,
)
from cg.services.file_delivery.file_formatter_service.delivery_file_formatting_service import (
    DeliveryFileFormattingService,
)
from cg.services.file_delivery.move_files_service.move_delivery_files_service import (
    MoveDeliveryFilesService,
)


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
        file_formatter_service: DeliveryFileFormattingService,
    ):
        self.file_manager = delivery_file_manager_service
        self.file_mover = move_file_service
        self.file_formatter = file_formatter_service

    @abstractmethod
    def deliver_files_for_case(self, case_id: str) -> None:
        """Deliver the files to the customer folder."""
        pass
