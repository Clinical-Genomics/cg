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
        missing_files: list[str] = []
        for sample in case.samples:
            sample_files: list[File] = self.housekeeper_api.files(
                bundle=sample.internal_id, tags={"bam"}
            ).all()
            missing_sample_files: list[str] = [
                file.full_path for file in sample_files if not Path(file.full_path).is_file()
            ]
            missing_files.extend(missing_sample_files)

        if missing_files:
            missing_files_str = "\n".join(missing_files)
            raise AnalysisNotReadyError(
                f"The following BAM files are missing: \n{missing_files_str}"
            )
