import logging
import os
from pathlib import Path

from cg.services.deliver_files.file_fetcher.models import SampleFile, CaseFile

LOG = logging.getLogger(__name__)


class FileManager:
    """
    Service to manage files.
    Handles operations that create or rename files and directories.
    """

    @staticmethod
    def create_directories(base_path: Path, directories: set[str]) -> None:
        """Create directories for given names under the base path."""

        for directory in directories:
            LOG.debug(f"[FileManager] Creating directory or file: {base_path}/{directory}")
            Path(base_path, directory).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def rename_file(src: Path, dst: Path) -> None:
        """Rename a file from src to dst."""
        LOG.debug(f"[FileManager] Renaming file: {src} -> {dst}")
        os.rename(src=src, dst=dst)

    @staticmethod
    def create_hard_link(src: Path, dst: Path) -> None:
        """Create a hard link from src to dst."""
        LOG.debug(f"[FileManager] Creating hard link: {src} -> {dst}")
        os.link(src=src, dst=dst)


class FileMover:
    """
    Service class to move files.
    Requires a file management service to perform file operations.
    """

    def __init__(self, file_manager):
        """
        :param file_manager: Service for file operations (e.g., create directories, move files).
        """
        self.file_management_service = file_manager

    def create_directories(self, base_path: Path, directories: set[str]) -> None:
        """Create required directories."""
        self.file_management_service.create_directories(base_path, directories)

    def move_files_to_directory(self, file_models: list, target_dir: Path) -> None:
        """Move files to the target directory."""
        for file_model in file_models:
            target_path = Path(target_dir, file_model.file_path.name)
            self._move_or_link_file(src=file_model.file_path, dst=target_path)

    @staticmethod
    def update_file_paths(
        file_models: list[CaseFile | SampleFile], target_dir: Path
    ) -> list[CaseFile | SampleFile]:
        """Update file paths to point to the target directory."""
        for file_model in file_models:
            file_model.file_path = Path(target_dir, file_model.file_path.name)
        return file_models

    def _move_or_link_file(self, src: Path, dst: Path) -> None:
        """Move or create a hard link for a file."""
        if dst.exists():
            LOG.debug(f"Overwriting existing file: {dst}")
            dst.unlink()
        self.file_management_service.create_hard_link(src=src, dst=dst)
