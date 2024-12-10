from pathlib import Path

from cg.services.deliver_files.file_fetcher.models import DeliveryFiles, SampleFile, CaseFile
from cg.services.deliver_files.file_mover.abstract import DestinationFilesMover
from cg.services.deliver_files.utils import FileMover


class BaseDestinationFilesMover(DestinationFilesMover):
    """
    Class to move files directly to the delivery base path.
    """

    def __init__(self, file_mover: FileMover):
        self.file_mover = file_mover

    def move_files(self, delivery_files: DeliveryFiles, delivery_base_path: Path) -> DeliveryFiles:
        """
        Move the files directly to the delivery base path.
        args:
            delivery_files: DeliveryFiles: The files to move.
            delivery_base_path: Path: The path to move the files to.
        """
        delivery_files.delivery_data.delivery_path = delivery_base_path
        delivery_files.case_files = self.file_mover.move_and_update_files(
            file_models=delivery_files.case_files, target_dir=delivery_base_path
        )
        delivery_files.sample_files = self.file_mover.move_and_update_files(
            file_models=delivery_files.sample_files, target_dir=delivery_base_path
        )
        return delivery_files
