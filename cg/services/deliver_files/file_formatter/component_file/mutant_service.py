import logging
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.services.deliver_files.file_fetcher.models import SampleFile
from cg.services.deliver_files.file_formatter.destination.models import FormattedFile
from cg.services.deliver_files.file_formatter.component_file.concatenation_service import (
    SampleFileConcatenationFormatter,
)
from cg.services.deliver_files.file_formatter.component_file.sample_service import FileManager

LOG = logging.getLogger(__name__)


class MutantFileFormatter:
    """
    Formatter for file to deliver or upload for the Mutant workflow.
    """

    def __init__(
        self,
        lims_api: LimsAPI,
        file_formatter: SampleFileConcatenationFormatter,
        file_manager: FileManager,
    ):
        self.lims_api: LimsAPI = lims_api
        self.file_formatter: SampleFileConcatenationFormatter = file_formatter
        self.file_manager = file_manager

    def format_files(
        self, moved_files: list[SampleFile], delivery_path: Path
    ) -> list[FormattedFile]:
        """
        Format the mutant files to deliver and return the formatted files.
        args:
            moved_files: The sample files to format
            delivery_path: The path to deliver the files

        """
        LOG.debug("[FORMAT SERVICE] Formatting and concatenating mutant files")
        formatted_files: list[FormattedFile] = self.file_formatter.format_files(
            moved_sample_files=moved_files, delivery_path=delivery_path
        )
        appended_formatted_files: list[FormattedFile] = self._add_lims_metadata_to_file_name(
            formatted_files=formatted_files, sample_files=moved_files
        )
        unique_formatted_files: list[FormattedFile] = self._filter_unique_path_combinations(
            appended_formatted_files
        )
        for unique_files in unique_formatted_files:
            self.file_manager.rename_file(
                src=unique_files.original_path, dst=unique_files.formatted_path
            )
        return unique_formatted_files

    def _add_lims_metadata_to_file_name(
        self, formatted_files: list[FormattedFile], sample_files: list[SampleFile]
    ) -> list[FormattedFile]:
        """
        This functions adds the region and lab code to the file name of the formatted files.
        Note: The region and lab code is fetched from LIMS using the sample id. It is required for delivery of the files.

        args:
            formatted_files: The formatted files to add the metadata to
            sample_files: The sample files to get the metadata from
        """
        appended_formatted_files: list[FormattedFile] = []
        for formatted_file in formatted_files:
            sample_id: str = self._get_sample_id_by_original_path(
                original_path=formatted_file.original_path, sample_files=sample_files
            )
            lims_meta_data = self.lims_api.get_sample_region_and_lab_code(sample_id)

            new_original_path: Path = formatted_file.formatted_path
            new_formatted_path = Path(
                formatted_file.formatted_path.parent,
                f"{lims_meta_data}{formatted_file.formatted_path.name}",
            )
            appended_formatted_files.append(
                FormattedFile(original_path=new_original_path, formatted_path=new_formatted_path)
            )
        return appended_formatted_files

    @staticmethod
    def _get_sample_id_by_original_path(original_path: Path, sample_files: list[SampleFile]) -> str:
        """Get the sample id by the original path of the sample file.
        args:
            original_path: The original path of the sample file
            sample_files: The list of sample files to search in
        """
        for sample_file in sample_files:
            if sample_file.file_path == original_path:
                return sample_file.sample_id
        raise ValueError(f"Could not find sample file with path {original_path}")

    @staticmethod
    def _filter_unique_path_combinations(
        formatted_files: list[FormattedFile],
    ) -> list[FormattedFile]:
        """
        Filter out duplicates from the formatted files list.

        note:
            During fastq concatenation Sample_R1 and Sample_R2 files are concatenated
            and moved to the same file Concat_Sample. This mean that there can be multiple entries
            for the same concatenated file in the formatted_files list
            coming from the SampleFileConcatenationService.
            This function filters out the duplicates to avoid moving the same file multiple times
            which would result in an error the second time since the files is no longer in the original path.

        args:
            formatted_files: The formatted files to filter
        """
        unique_combinations = set()
        unique_files: list[FormattedFile] = []
        for formatted_file in formatted_files:
            combination = (formatted_file.original_path, formatted_file.formatted_path)
            if combination not in unique_combinations:
                unique_combinations.add(combination)
                unique_files.append(formatted_file)
        return unique_files
