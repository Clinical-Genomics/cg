from pathlib import Path

from cg.apps.tb import TrailblazerAPI
from cg.constants import FileExtensions
from cg.constants.constants import WorkflowManager
from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter
from cg.services.analysis_starter.tracker.tracker import Tracker
from cg.store.models import Case
from cg.store.store import Store


class MicrosaltTracker(Tracker):
    def __init__(
        self,
        store: Store,
        subprocess_submitter: SubprocessSubmitter,
        trailblazer_api: TrailblazerAPI,
        workflow_root: str,
    ):
        super().__init__(store=store, trailblazer_api=trailblazer_api, workflow_root=workflow_root)
        self.subprocess_submitter = subprocess_submitter

    def _workflow_manager(self) -> WorkflowManager:
        return WorkflowManager.Slurm

    def _get_job_ids_path(self, case_id: str) -> Path:
        project_id: str = self._get_file_name_start(case_id)
        return Path(
            self.workflow_root,
            "results",
            "reports",
            "trailblazer",
            f"{project_id}_slurm_ids{FileExtensions.YAML}",
        )

    def _get_file_name_start(self, case_id: str) -> str:
        """Returns the LIMS project id if the case contains multiple samples, else the sample id."""
        case: Case = self.store.get_case_by_internal_id(case_id)
        sample_id: str = case.samples[0].internal_id
        if len(case.samples) == 1:
            return sample_id
        return self._extract_project_id(sample_id)

    @staticmethod
    def _extract_project_id(sample_id: str) -> str:
        return sample_id.rsplit("A", maxsplit=1)[0]

    def _get_workflow_version(self, case_config: MicrosaltCaseConfig) -> str:
        return self.subprocess_submitter.get_workflow_version(case_config)
