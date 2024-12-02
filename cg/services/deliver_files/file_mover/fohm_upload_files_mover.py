from pathlib import Path

from cg.services.deliver_files.file_fetcher.models import DeliveryFiles
from cg.services.deliver_files.utils import FileMover


class GenericFilesMover:
    """
    Class to move files directly to the delivery base path.
    """

    def __init__(self, file_mover: FileMover):
        self.file_mover = file_mover

    def move_files(self, delivery_files: DeliveryFiles, delivery_base_path: Path) -> DeliveryFiles:
        """Move the files directly to the delivery base path."""
        if delivery_files.case_files:
            self.file_mover.move_files_to_directory(delivery_files.case_files, delivery_base_path)
            delivery_files.case_files = self.file_mover.update_file_paths(
                delivery_files.case_files, delivery_base_path
            )
        self.file_mover.move_files_to_directory(delivery_files.sample_files, delivery_base_path)
        delivery_files.sample_files = self.file_mover.update_file_paths(
            delivery_files.sample_files, delivery_base_path
        )
        return delivery_files
