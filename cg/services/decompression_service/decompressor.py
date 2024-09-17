import zipfile
from pathlib import Path


class Decompressor:

    def decompress(self, source_path: Path, destination_path: Path) -> Path:
        """Decompress a file to a directory."""
        with zipfile.ZipFile(source_path, "r") as zip_file:
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
