from pathlib import Path

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.exc import AnalysisNotReadyError
from cg.services.analysis_starter.analysis_input_validator.analysis_input_validator import (
    AnalysisInputValidator,
)
from cg.store.models import Case
from cg.store.store import Store


class DataExistsValidator(AnalysisInputValidator):
    def __init__(self, housekeeper_api: HousekeeperAPI, status_db: Store) -> None:
        self.housekeeper_api = housekeeper_api
        self.status_db = status_db

    def ensure_files_are_ready(self, case_id: str) -> None:
        case: Case = self.status_db.get_case_by_internal_id_strict(case_id)
        tags = self._get_raw_data_tags_for_workflow(case.data_analysis)
        samples_without_files: list[str] = self._get_samples_without_files(case=case, tags=tags)
        missing_files: list[str] = self._get_missing_file_paths(case=case, tags=tags)
        if samples_without_files or missing_files:
            self._raise_error(
                missing_files=missing_files, samples_without_files=samples_without_files
            )

    def _get_samples_without_files(self, case: Case, tags: set[str]) -> list[str]:
        samples_without_files: list[str] = []
        for sample in case.samples:
            sample_files: list[File] = self.housekeeper_api.files(
                bundle=sample.internal_id, tags=tags
            ).all()
            if not sample_files:
                samples_without_files.append(sample.internal_id)
        return samples_without_files

    def _get_missing_file_paths(self, case: Case, tags: set[str]) -> list[str]:
        missing_files: list[str] = []
        for sample in case.samples:
            sample_files: list[File] = self.housekeeper_api.files(
                bundle=sample.internal_id, tags=tags
            ).all()
            missing_sample_files: list[str] = [
                file.full_path for file in sample_files if not Path(file.full_path).is_file()
            ]
            missing_files.extend(missing_sample_files)
        return missing_files

    @staticmethod
    def _raise_error(missing_files: list[str], samples_without_files: list[str]) -> None:
        error_message = ""
        if samples_without_files:
            samples_without_files_str = "\n".join(samples_without_files)
            error_message += f"The following samples are missing raw data in Housekeeper: \n{samples_without_files_str}"
        if missing_files:
            missing_files_str = "\n".join(missing_files)
            error_message += (
                f"\nThe following raw data files are missing on disk: \n{missing_files_str}"
            )
        raise AnalysisNotReadyError(error_message)

    def _get_raw_data_tags_for_workflow(self, workflow: Workflow) -> set[str]:
        match workflow:
            case Workflow.NALLO:
                return {SequencingFileTag.BAM}
            case Workflow.TRANA_16S | Workflow.TRANA_ITS:
                return {SequencingFileTag.FASTQ}
            case _:
                raise NotImplementedError
