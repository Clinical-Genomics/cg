import logging
import zipfile
from pathlib import Path

LOG = logging.getLogger(__name__)


class Decompressor:

    def decompress(self, source_path: Path, destination_path: Path) -> Path:
        """Decompress a file to a directory."""
        if not source_path.exists():
            raise FileNotFoundError(f"Source path {source_path} does not exist.")
        with zipfile.ZipFile(source_path, "r") as zip_file:
            LOG.debug(f"Decompressing {source_path} to {destination_path}")
            zip_file.extractall(destination_path)
        if not self._decompressed_path_exists(destination_path):
            raise FileNotFoundError(
                f"Decompressed path {destination_path} does not exist, something went wrong."
            )
        return destination_path

    @staticmethod
    def _decompressed_path_exists(destination_path: Path) -> bool:
        """Check if the decompressed path already exists."""
        return destination_path.exists()
