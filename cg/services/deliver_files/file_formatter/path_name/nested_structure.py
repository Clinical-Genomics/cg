from pathlib import Path

from cg.services.deliver_files.file_formatter.files.sample_service import LOG
from cg.services.deliver_files.file_formatter.path_name.abstract import PathNameFormatter


class NestedStructurePathFormatter(PathNameFormatter):
    """
    Class to format sample file names and paths in a nested format used to deliver files to a customer inbox.
    """

    def format_file_path(self, file_path: Path, provided_id: str, provided_name: str) -> Path:
        """
        Returns formatted files with original and formatted file names:
        1. Adds a folder with provided name to the path of the files.
        2. Replaces id by name.

        args:
            file_path: The path to the file
            provided_id: The id to replace
            provided_name: The name to replace the id with
        """
        LOG.debug("[FORMAT SERVICE] Formatting sample file names with nested structure.")
        replaced_name = file_path.name.replace(provided_id, provided_name)
        formatted_path = Path(file_path.parent, provided_name, replaced_name)
        return formatted_path
