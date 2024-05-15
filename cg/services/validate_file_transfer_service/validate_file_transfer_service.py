from pathlib import Path

from cg.io.controller import ReadFile
from cg.utils.files import get_file_in_directory, get_files_in_directory_with_pattern


class ValidateFileTransferService:
    """Service to validate file transfers."""

    @staticmethod
    def get_manifest_file_content(manifest_file: Path, manifest_file_format: str) -> dict:
        """Get the content of the manifest file."""
        file_reader = ReadFile()
        return file_reader.get_content_from_file(
            file_format=manifest_file_format, file_path=manifest_file
        )

    @staticmethod
    def extract_file_names_from_manifest(manifest_content: any) -> list[str]:
        """
        Extract the file paths from the manifest content.
        A file path is expected to contain at least one '/' character.
        """
        file_names: list[str] = []
        for line in manifest_content:
            if "/" in line:
                formatted_line: str = line.rstrip()
                file_names.append(Path(formatted_line).name)
        return file_names

    @staticmethod
    def is_file_in_directory_tree(file_name: str, source_dir: Path) -> bool:
        """Check if a file is present in the directory tree."""
        try:
            if get_file_in_directory(directory=source_dir, file_name=file_name):
                return True
        except FileNotFoundError:
            return False

    @staticmethod
    def get_manifest_file_paths(source_dir: Path, pattern: str) -> list[Path]:
        return get_files_in_directory_with_pattern(directory=source_dir, pattern=pattern)

    def validate_by_manifest_file(
        self, manifest_file: Path, source_dir: Path, manifest_file_format: str
    ) -> bool:
        """Validate all files listed in the manifest are present in the directory tree."""
        manifest_content: any = self.get_manifest_file_content(
            manifest_file=manifest_file, manifest_file_format=manifest_file_format
        )
        files_to_validate: list[str] = self.extract_file_names_from_manifest(manifest_content)
        for file_name in files_to_validate:
            if not self.is_file_in_directory_tree(file_name=file_name, source_dir=source_dir):
                return False
        return True
