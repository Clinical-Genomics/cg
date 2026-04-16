from pathlib import Path

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import AnalysisNotReadyError
from cg.services.analysis_starter.input_fetcher.input_fetcher import InputFetcher
from cg.store.models import Case
from cg.store.store import Store


class BamFetcher(InputFetcher):
    def __init__(self, housekeeper_api: HousekeeperAPI, status_db: Store) -> None:
        self.housekeeper_api = housekeeper_api
        self.status_db = status_db

    def ensure_files_are_ready(self, case_id: str) -> None:
        case: Case = self.status_db.get_case_by_internal_id_strict(case_id)
        samples_without_files: list[str] = self._get_samples_without_files(case)
        missing_files: list[str] = self._get_missing_file_paths(case)
        if samples_without_files or missing_files:
            self._raise_error(
                missing_files=missing_files, samples_without_files=samples_without_files
            )

    def _get_samples_without_files(self, case: Case) -> list[str]:
        samples_without_files: list[str] = []
        for sample in case.samples:
            sample_files: list[File] = self.housekeeper_api.files(
                bundle=sample.internal_id, tags={"bam"}
            ).all()
            if not sample_files:
                samples_without_files.append(sample.internal_id)
        return samples_without_files

    def _get_missing_file_paths(self, case: Case) -> list[str]:
        missing_files: list[str] = []
        for sample in case.samples:
            sample_files: list[File] = self.housekeeper_api.files(
                bundle=sample.internal_id, tags={"bam"}
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
            error_message += f"The following samples are missing BAM files in Housekeeper: \n{samples_without_files_str}"
        if missing_files:
            missing_files_str = "\n".join(missing_files)
            error_message += f"\nThe following BAM files are missing on disk: \n{missing_files_str}"
        raise AnalysisNotReadyError(error_message)
