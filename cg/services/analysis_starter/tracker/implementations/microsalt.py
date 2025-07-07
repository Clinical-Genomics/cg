from pathlib import Path

from cg.constants import FileExtensions
from cg.constants.constants import WorkflowManager
from cg.services.analysis_starter.tracker.tracker import Tracker
from cg.store.models import Case


class MicrosaltTracker(Tracker):

    def _workflow_manager(self) -> WorkflowManager:
        return WorkflowManager.Slurm

    def _get_job_ids_path(self, case_id: str) -> Path:
        project_id: str = self._get_file_name_start(case_id)
        job_ids_path = Path(
            self.workflow_root,
            "results",
            "reports",
            "trailblazer",
            f"{project_id}_slurm_ids{FileExtensions.YAML}",
        )
        # Necessary due to how microsalt structures its output
        self._ensure_old_job_ids_are_removed(job_ids_path)
        return job_ids_path

    def _get_file_name_start(self, case_id: str) -> str:
        """Returns the LIMS project if the case contains multiple samples, else the sample id."""
        case: Case = self.store.get_case_by_internal_id(case_id)
        sample_id: str = case.samples[0].internal_id
        if len(case.samples) == 1:
            return sample_id
        return self._extract_project_id(sample_id)

    @staticmethod
    def _extract_project_id(sample_id: str) -> str:
        return sample_id.rsplit("A", maxsplit=1)[0]

    @staticmethod
    def _ensure_old_job_ids_are_removed(job_ids_path: Path) -> None:
        is_yaml_file: bool = job_ids_path.suffix == FileExtensions.YAML
        if job_ids_path.exists() and is_yaml_file:
            job_ids_path.unlink()
