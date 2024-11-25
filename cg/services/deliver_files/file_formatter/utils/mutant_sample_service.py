from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.services.deliver_files.file_fetcher.models import SampleFile
from cg.services.deliver_files.file_formatter.models import FormattedFile
from cg.services.deliver_files.file_formatter.utils.sample_concatenation_service import (
    SampleFileConcatenationFormatter,
)
from cg.services.deliver_files.file_formatter.utils.sample_service import FileManagingService


class MutantFileFormatter:
    def __init__(
        self,
        lims_api: LimsAPI,
        file_formatter: SampleFileConcatenationFormatter,
        file_manager: FileManagingService,
    ):
        self.lims_api: LimsAPI = lims_api
        self.file_formatter: SampleFileConcatenationFormatter = file_formatter
        self.file_manager = file_manager

    def format_files(
        self, moved_files: list[SampleFile], ticket_dir_path: Path
    ) -> list[FormattedFile]:
        formatted_files: list[FormattedFile] = self.file_formatter.format_files(
            moved_files=moved_files, ticket_dir_path=ticket_dir_path
        )
        formatted_files = self._add_lims_metadata_to_file_name(
            formatted_files=formatted_files, sample_files=moved_files
        )
        unique_formatted_files = self._filter_unique_path_combinations(formatted_files)
        for unique_files in unique_formatted_files:
            self.file_manager.rename_file(
                src=unique_files.original_path, dst=unique_files.formatted_path
            )
        return unique_formatted_files

    def _add_lims_metadata_to_file_name(
        self, formatted_files: list[FormattedFile], sample_files: list[SampleFile]
    ) -> list[FormattedFile]:
        """This functions adds the region and lab code to the file name of the formatted files."""
        for formatted_file in formatted_files:
            sample_id: str = self._get_sample_id_by_original_path(
                original_path=formatted_file.original_path, sample_files=sample_files
            )
            lims_meta_data = self.lims_api.get_sample_region_and_lab_code(sample_id)
            formatted_file.original_path = formatted_file.formatted_path
            formatted_file.formatted_path = Path(
                formatted_file.formatted_path.parent,
                f"{lims_meta_data}{formatted_file.formatted_path.name}",
            )
        return formatted_files

    @staticmethod
    def _get_sample_id_by_original_path(original_path: Path, sample_files: list[SampleFile]) -> str:
        for sample_file in sample_files:
            if sample_file.file_path == original_path:
                return sample_file.sample_id
        raise ValueError(f"Could not find sample file with path {original_path}")

    @staticmethod
    def _filter_unique_path_combinations(
        formatted_files: list[FormattedFile],
    ) -> list[FormattedFile]:
        """
        During fastq concatenation Sample_R1 and Sample_R2 files are concatenated and moved to the same file Concat_Sample.
        This mean that there can be multiple entries for the same concatenated file in the formatted_files list coming
        from the SampleFileConcatenationService.
        This function filters out the duplicates to avoid moving the same file multiple times
        which would result in an error the second time since the files is no longer in the original path.
        """
        unique_combinations = set()
        unique_files = []
        for formatted_file in formatted_files:
            combination = (formatted_file.original_path, formatted_file.formatted_path)
            if combination not in unique_combinations:
                unique_combinations.add(combination)
                unique_files.append(formatted_file)
        return unique_files
