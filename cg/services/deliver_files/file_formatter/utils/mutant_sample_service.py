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


class MutantFileFormatter(SampleFileConcatenationFormatter):
    def __init__(self, lims_api: LimsAPI, concatenation_service: FastqConcatenationService):
        self.lims_api: LimsAPI = lims_api
        super().__init__(concatenation_service=concatenation_service)

    def format_files(
        self, moved_files: list[SampleFile], ticket_dir_path: Path
    ) -> list[FormattedFile]:
        formatted_files: list[FormattedFile] = super().format_files(
            moved_files=moved_files, ticket_dir_path=ticket_dir_path
        )
        formatted_files = self._add_lims_metadata(
            formatted_files=formatted_files, sample_files=moved_files
        )
        unique_formatted_files = self._filter_unique_path_combinations(formatted_files)
        return self._format_sample_files(unique_formatted_files)

    def _get_lims_naming_metadata(self, sample_id: str) -> str:
        region_code = self.lims_api.get_sample_attribute(
            lims_id=sample_id, key="region_code"
        ).split(" ")[0]
        lab_code = self.lims_api.get_sample_attribute(lims_id=sample_id, key="lab_code").split(" ")[
            0
        ]
        return f"{region_code}_{lab_code}_"

    def _add_lims_metadata(
        self, formatted_files: list[FormattedFile], sample_files: list[SampleFile]
    ) -> list[FormattedFile]:
        for formatted_file in formatted_files:
            sample_id: str = self._get_sample_id_by_original_path(
                original_path=formatted_file.original_path, sample_files=sample_files
            )
            lims_meta_data = self._get_lims_naming_metadata(sample_id)
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
        unique_combinations = set()
        unique_files = []
        for formatted_file in formatted_files:
            combination = (formatted_file.original_path, formatted_file.formatted_path)
            if combination not in unique_combinations:
                unique_combinations.add(combination)
                unique_files.append(formatted_file)
        return unique_files
