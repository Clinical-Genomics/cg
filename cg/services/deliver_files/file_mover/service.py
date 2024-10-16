import logging
from pathlib import Path

from cg.constants.delivery import INBOX_NAME
from cg.services.deliver_files.file_fetcher.models import (
    CaseFile,
    DeliveryFiles,
    DeliveryMetaData,
    SampleFile,
)
from cg.utils.files import link_or_overwrite_file

LOG = logging.getLogger(__name__)


class DeliveryFilesMover:
    """
    Class that encapsulates the logic required for moving files to the customer folder.
    """

    def move_files(self, delivery_files: DeliveryFiles, delivery_base_path: Path) -> DeliveryFiles:
        """Move the files to the customer folder."""
        inbox_ticket_dir_path: Path = self._create_ticket_inbox_dir_path(
            delivery_base_path=delivery_base_path, delivery_data=delivery_files.delivery_data
        )
        delivery_files.delivery_data.customer_ticket_inbox = inbox_ticket_dir_path
        self._create_ticket_inbox_folder(inbox_ticket_dir_path)
        self._create_hard_links_for_delivery_files(
            delivery_files=delivery_files, inbox_dir_path=inbox_ticket_dir_path
        )
        return self._replace_file_paths_with_inbox_dir_paths(
            delivery_files=delivery_files, inbox_dir_path=inbox_ticket_dir_path
        )

    @staticmethod
    def _create_ticket_inbox_folder(
        inbox_ticket_dir_path: Path,
    ) -> Path:
        """Create a ticket inbox folder in the customer folder, overwrites if already present."""
        LOG.debug(f"[MOVE SERVICE] Creating ticket inbox folder: {inbox_ticket_dir_path}")
        inbox_ticket_dir_path.mkdir(parents=True, exist_ok=True)
        return inbox_ticket_dir_path

    @staticmethod
    def _create_ticket_inbox_dir_path(
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
    def _create_inbox_file_path(file_path: Path, inbox_dir_path: Path) -> Path:
        """Create the path to the inbox file."""
        return Path(inbox_dir_path, file_path.name)

    def _create_hard_link_file_paths(
        self, file_models: list[SampleFile | CaseFile], inbox_dir_path: Path
    ) -> None:
        """Create hard links to the sample files in the customer folder."""
        for file_model in file_models:
            inbox_file_path: Path = self._create_inbox_file_path(
                file_path=file_model.file_path, inbox_dir_path=inbox_dir_path
            )
            link_or_overwrite_file(src=file_model.file_path, dst=inbox_file_path)

    def _create_hard_links_for_delivery_files(
        self, delivery_files: DeliveryFiles, inbox_dir_path: Path
    ) -> None:
        """Create hard links to the files in the customer folder."""
        LOG.debug(f"[MOVE SERVICE] Creating hard links for delivery files in: {inbox_dir_path}")
        if delivery_files.case_files:
            self._create_hard_link_file_paths(
                file_models=delivery_files.case_files, inbox_dir_path=inbox_dir_path
            )
        self._create_hard_link_file_paths(
            file_models=delivery_files.sample_files, inbox_dir_path=inbox_dir_path
        )

    def _replace_file_path_with_inbox_dir_path(
        self, file_models: list[SampleFile | CaseFile], inbox_dir_path: Path
    ) -> list[SampleFile | CaseFile]:
        """Replace the file path with the inbox path."""
        for file_model in file_models:
            inbox_file_path: Path = self._create_inbox_file_path(
                file_path=file_model.file_path, inbox_dir_path=inbox_dir_path
            )
            file_model.file_path = inbox_file_path
        return file_models

    def _replace_file_paths_with_inbox_dir_paths(
        self,
        delivery_files: DeliveryFiles,
        inbox_dir_path: Path,
    ) -> DeliveryFiles:
        """
        Replace to original file paths in the delivery files with the customer inbox file paths.
        """
        LOG.debug(f"[MOVE SERVICE] Replacing file paths with inbox dir path: {inbox_dir_path}")
        if delivery_files.case_files:
            delivery_files.case_files = self._replace_file_path_with_inbox_dir_path(
                file_models=delivery_files.case_files, inbox_dir_path=inbox_dir_path
            )
        delivery_files.sample_files = self._replace_file_path_with_inbox_dir_path(
            file_models=delivery_files.sample_files, inbox_dir_path=inbox_dir_path
        )
        return delivery_files
