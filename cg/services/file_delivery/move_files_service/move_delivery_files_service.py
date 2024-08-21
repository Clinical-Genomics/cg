from abc import abstractmethod, ABC
from pathlib import Path

# Exchan

from cg.constants.delivery import INBOX_NAME
from cg.services.file_delivery.fetch_file_service.models import (
    DeliveryFiles,
    DeliveryMetaData,
    CaseFile,
    SampleFile,
)
from cg.utils.files import link_or_overwrite_file


class MoveDeliveryFilesService:
    """
    Class that encapsulates the logic required for moving files to the customer folder.
    """

    def move_files(self, delivery_files: DeliveryFiles, delivery_base_path: Path) -> DeliveryFiles:
        """Move the files to the customer folder."""
        inbox_path: Path = self._create_ticket_inbox_path(
            delivery_base_path, delivery_files.delivery_data
        )
        self._create_ticket_inbox_folder(inbox_path)
        self._create_hard_links_for_delivery_files(
            delivery_files=delivery_files, inbox_path=inbox_path
        )
        return self._replace_file_paths_with_inbox_paths(
            delivery_files=delivery_files, inbox_path=inbox_path
        )

    @staticmethod
    def _create_ticket_inbox_folder(
        inbox_path: Path,
    ) -> Path:
        """Create a ticket inbox folder in the customer folder."""
        if not inbox_path.exists():
            inbox_path.mkdir(parents=True)
            return inbox_path
        raise FileExistsError(f"Ticket inbox folder {inbox_path} already exists for ticket.")

    @staticmethod
    def _create_ticket_inbox_path(
        delivery_base_path: Path, delivery_data: DeliveryMetaData
    ) -> Path:
        """Create the path to the ticket inbox folder."""
        return Path(
            delivery_base_path,
            delivery_data.customer_internal_id,
            INBOX_NAME,
            delivery_data.ticket_id,
        )

    @staticmethod
    def _create_inbox_file_path(file_path: Path, inbox_path: Path) -> Path:
        """Create the path to the inbox file."""
        return Path(inbox_path, file_path.name)

    def _create_hard_link_file_paths(
        self, file_models: list[SampleFile | CaseFile], inbox_path: Path
    ) -> None:
        """Create hard links to the sample files in the customer folder."""
        for file_model in file_models:
            inbox_file_path: Path = self._create_inbox_file_path(
                file_path=file_model.file_path, inbox_path=inbox_path
            )
            link_or_overwrite_file(src=file_model.file_path, dst=inbox_file_path)

    def _create_hard_links_for_delivery_files(
        self, delivery_files: DeliveryFiles, inbox_path: Path
    ) -> None:
        """Create hard links to the files in the customer folder."""
        if delivery_files.case_files:
            self._create_hard_link_file_paths(
                file_models=delivery_files.case_files, inbox_path=inbox_path
            )
        self._create_hard_link_file_paths(
            file_models=delivery_files.sample_files, inbox_path=inbox_path
        )

    def _replace_file_path_with_inbox_path(
        self, file_models: list[SampleFile | CaseFile], inbox_path: Path
    ) -> list[SampleFile | CaseFile]:
        """Replace the file path with the inbox path."""
        for file_model in file_models:
            inbox_file_path: Path = self._create_inbox_file_path(
                file_path=file_model.file_path, inbox_path=inbox_path
            )
            file_model.file_path = inbox_file_path
        return file_models

    def _replace_file_paths_with_inbox_paths(
        self,
        delivery_files: DeliveryFiles,
        inbox_path: Path,
    ) -> DeliveryFiles:
        """Replace the file paths with the inbox paths."""
        if delivery_files.case_files:
            delivery_files.case_files = self._replace_file_path_with_inbox_path(
                file_models=delivery_files.case_files, inbox_path=inbox_path
            )
        delivery_files.sample_files = self._replace_file_path_with_inbox_path(
            file_models=delivery_files.sample_files, inbox_path=inbox_path
        )
        return delivery_files
