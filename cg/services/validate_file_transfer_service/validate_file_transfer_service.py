import logging
from pathlib import Path

from cg.io.controller import ReadFile
from cg.utils.files import get_file_in_directory, get_files_in_directory_with_pattern

LOG = logging.getLogger(__name__)


class ValidateFileTransferService:
    """Service to validate file transfers via a manifest file."""

    def validate_file_transfer(
        self, manifest_file: Path, source_dir: Path, manifest_file_format: str
    ):
        """Validate all files listed in the manifest are present in the directory tree."""
        files_in_manifest: list[str] = self._get_files_in_manifest(
            manifest_file=manifest_file, manifest_file_format=manifest_file_format
        )
        if not self._are_all_files_present(
            files_to_validate=files_in_manifest, source_dir=source_dir
        ):
            raise FileNotFoundError(
                f"Not all files listed in the manifest file {manifest_file} are present in the directory tree {source_dir}"
            )
        LOG.debug("File transfer validated")
        return

    @staticmethod
    def _get_manifest_file_content(manifest_file: Path, manifest_file_format: str) -> list[str]:
        """Get the content of the manifest file."""
        file_reader = ReadFile()
        return file_reader.get_content_from_file(
            file_format=manifest_file_format, file_path=manifest_file
        )

    @staticmethod
    def _is_valid_path(line: str):
        return "/" in line

    def _extract_file_names_from_manifest(self, manifest_content: any) -> list[str]:
        """
        Extract the file paths from the manifest content.
        A file path is expected to contain at least one '/' character.
        """
        file_names: list[str] = []
        for line in manifest_content:
            if self._is_valid_path(line):
                formatted_line: str = line.rstrip()
                file_names.append(Path(formatted_line).name)
        return file_names

    @staticmethod
    def _is_file_in_directory_tree(file_name: str, source_dir: Path) -> bool:
        """Check if a file is present in the directory tree."""
        try:
            if get_file_in_directory(directory=source_dir, file_name=file_name):
                return True
        except FileNotFoundError:
            return False

    @staticmethod
    def _get_manifest_file_paths(source_dir: Path, pattern: str) -> list[Path]:
        return get_files_in_directory_with_pattern(directory=source_dir, pattern=pattern)

    def _get_files_in_manifest(self, manifest_file: Path, manifest_file_format: str) -> list[str]:
        """Get the files listed in the manifest file."""
        manifest_content: list[str] = self._get_manifest_file_content(
            manifest_file=manifest_file, manifest_file_format=manifest_file_format
        )
        return self._extract_file_names_from_manifest(manifest_content)

    def _are_all_files_present(self, files_to_validate: list[str], source_dir: Path) -> bool:
        """Check if all files are present in the directory tree."""
        for file_name in files_to_validate:
            if not self._is_file_in_directory_tree(file_name=file_name, source_dir=source_dir):
                return False
        return True
