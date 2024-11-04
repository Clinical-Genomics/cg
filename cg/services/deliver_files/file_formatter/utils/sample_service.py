import os
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.services.deliver_files.file_fetcher.models import SampleFile
from cg.services.deliver_files.file_formatter.models import FormattedFile
from cg.services.deliver_files.file_formatter.utils.sample_concatenation_service import (
    SampleFileConcatenationFormatter,
)
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)


class SampleFileFormatter:
    """
    Format the sample files to deliver.
    Used for all workflows except Microsalt and Mutant.
    """

    def format_files(
        self, moved_files: list[SampleFile], ticket_dir_path: Path
    ) -> list[FormattedFile]:
        """Format the sample files to deliver and return the formatted files."""
        sample_names: set[str] = self._get_sample_names(moved_files)
        self._create_sample_folders(ticket_dir_path=ticket_dir_path, sample_names=sample_names)
        return self._format_sample_files(moved_files)

    @staticmethod
    def _get_sample_names(sample_files: list[SampleFile]) -> set[str]:
        return set(sample_file.sample_name for sample_file in sample_files)

    @staticmethod
    def _create_sample_folders(ticket_dir_path: Path, sample_names: set[str]):
        for sample_name in sample_names:
            sample_dir_path = Path(ticket_dir_path, sample_name)
            sample_dir_path.mkdir(exist_ok=True)

    def _format_sample_files(self, sample_files: list[SampleFile]) -> list[FormattedFile]:
        formatted_files: list[FormattedFile] = self._get_formatted_files(sample_files)
        for formatted_file in formatted_files:
            os.rename(src=formatted_file.original_path, dst=formatted_file.formatted_path)
        return formatted_files

    @staticmethod
    def _get_formatted_files(sample_files: list[SampleFile]) -> list[FormattedFile]:
        """
        Returns formatted files:
        1. Adds a folder with sample name to the path of the sample files.
        2. Replaces sample id by sample name.
        """
        formatted_files: list[FormattedFile] = []
        for sample_file in sample_files:
            replaced_sample_file_name: str = sample_file.file_path.name.replace(
                sample_file.sample_id, sample_file.sample_name
            )
            formatted_file_path = Path(
                sample_file.file_path.parent, sample_file.sample_name, replaced_sample_file_name
            )
            formatted_files.append(
                FormattedFile(
                    original_path=sample_file.file_path, formatted_path=formatted_file_path
                )
            )
        return formatted_files


class MutantFileFormatter(SampleFileConcatenationFormatter):
    def __init__(self, lims_api: LimsAPI, concatenation_service: FastqConcatenationService):
        self.lims_api: LimsAPI = lims_api
        super().__init__(concatenation_service = concatenation_service)
    
    def format_files(self, moved_files: list[SampleFile], ticket_dir_path: Path
    ) -> list[FormattedFile]:
        formatted_files: list[FormattedFile] = super().format_files(
            moved_files=moved_files, ticket_dir_path=ticket_dir_path
        )
        formatted_files = self._add_lims_metadata(formatted_files)
        return self._format_sample_files(formatted_files)
    
    def _get_lims_naming_metadata(self, sample_id: str)-> str:

        region_code = self.lims_api.get_sample_attribute(lims_id=sample_id, key="region_code").split(" ")[0]
        lab_code = self.lims_api.get_sample_attribute(lims_id=sample_id, key="lab_code").split(" ")[0]
    
        return f"{region_code}_{lab_code}"

    def _add_lims_metadata(self, formatted_files: list[FormattedFile], sample_files: list[SampleFile]) -> list[FormattedFile]:
        for formatted_file in formatted_files:
            lims_meta_data = self._get_lims_naming_metadata(sample_id = self._get_sample_id_by_original_path(formatted_file.original_path, sample_files))
            formatted_file.original_path = formatted_file.formatted_path
            formatted_file.formatted_path = lims_meta_data + formatted_file.formatted_path
        return formatted_files
    
    def _get_sample_id_by_original_path(original_path: Path, sample_files: list[SampleFile])-> str:
        for sample_file in sample_files:
            if sample_file.file_path == original_path:
                return sample_file.sample_id
        raise ValueError(f"Could not find sample file with path {original_path}")



