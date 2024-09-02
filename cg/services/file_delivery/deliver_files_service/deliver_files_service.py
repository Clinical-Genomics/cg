from pathlib import Path
from cg.services.file_delivery.fetch_file_service.fetch_delivery_files_service import (
    FetchDeliveryFilesService,
)
from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles
from cg.services.file_delivery.file_formatter_service.delivery_file_formatting_service import (
    DeliveryFileFormattingService,
)
from cg.services.file_delivery.move_files_service.move_delivery_files_service import (
    MoveDeliveryFilesService,
)
from cg.store.exc import EntryNotFoundError
from cg.store.models import Case
from cg.store.store import Store


class DeliverFilesService:
    """
    Deliver files to the customer inbox on hasta.
    1. Get the files to deliver from Housekeeper based on workflow and data delivery
    2. Create a delivery folder structure in the customer folder on Hasta and move the files there
    3. Reformatting of output / renaming of files
    """

    def __init__(
        self,
        delivery_file_manager_service: FetchDeliveryFilesService,
        move_file_service: MoveDeliveryFilesService,
        file_formatter_service: DeliveryFileFormattingService,
        status_db: Store,
    ):
        self.file_manager = delivery_file_manager_service
        self.file_mover = move_file_service
        self.file_formatter = file_formatter_service
        self.status_db = status_db

    def deliver_files_for_case(self, case_id: str, delivery_base_path: Path) -> None:
        """Deliver the files for a case to the customer folder."""
        delivery_files: DeliveryFiles = self.file_manager.get_files_to_deliver(case_id)
        moved_files: DeliveryFiles = self.file_mover.move_files(
            delivery_files=delivery_files, delivery_base_path=delivery_base_path
        )
        self.file_formatter.format_files(moved_files)

    def deliver_files_for_ticket(self, ticket_id: str, delivery_base_path: Path) -> None:
        """Deliver the files for all cases in a ticket to the customer folder."""
        cases: list[Case] = self.status_db.get_cases_by_ticket_id(ticket_id)
        if not cases:
            raise EntryNotFoundError(f"No cases found for ticket {ticket_id}")
        for case in cases:
            self.deliver_files_for_case(
                case_id=case.internal_id, delivery_base_path=delivery_base_path
            )
