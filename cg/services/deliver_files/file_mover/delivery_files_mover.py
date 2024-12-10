import logging
from pathlib import Path

from cg.constants.delivery import INBOX_NAME
from cg.services.deliver_files.file_fetcher.models import (
    DeliveryFiles,
    DeliveryMetaData,
)
from cg.services.deliver_files.utils import FileMover

LOG = logging.getLogger(__name__)


class CustomerInboxFilesMover:
    """
    Class to move files to the customer folder.
    """

    def __init__(self, file_mover: FileMover):
        self.file_mover = file_mover

    def move_files(self, delivery_files: DeliveryFiles, delivery_base_path: Path) -> DeliveryFiles:
        """Move the files to the customer folder."""

        inbox_ticket_dir_path = self._create_ticket_inbox_dir_path(
            delivery_base_path=delivery_base_path, delivery_data=delivery_files.delivery_data
        )
        delivery_files.delivery_data.customer_ticket_inbox = inbox_ticket_dir_path

        self.file_mover.create_directories(
            base_path=delivery_base_path,
            directories={str(inbox_ticket_dir_path.relative_to(delivery_base_path))},
        )
        if delivery_files.case_files:
            self.file_mover.move_files_to_directory(
                file_models=delivery_files.case_files, target_dir=inbox_ticket_dir_path
            )
            delivery_files.case_files = self.file_mover.update_file_paths(
                file_models=delivery_files.case_files, target_dir=inbox_ticket_dir_path
            )
        self.file_mover.move_files_to_directory(
            file_models=delivery_files.sample_files, target_dir=inbox_ticket_dir_path
        )
        delivery_files.sample_files = self.file_mover.update_file_paths(
            file_models=delivery_files.sample_files, target_dir=inbox_ticket_dir_path
        )

        return delivery_files

    @staticmethod
    def _create_ticket_inbox_dir_path(
        delivery_base_path: Path, delivery_data: DeliveryMetaData
    ) -> Path:
        """Generate the path to the ticket inbox directory."""
        return Path(
            delivery_base_path,
            delivery_data.customer_internal_id,
            INBOX_NAME,
            delivery_data.ticket_id,
        )
