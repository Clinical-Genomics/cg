from pathlib import Path

from cg.constants.constants import WorkflowManager
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.tracker.tracker import Tracker


class NextflowTracker(Tracker):
    def _workflow_manager(self) -> WorkflowManager:
        return WorkflowManager.Tower

    def _get_job_ids_path(self, case_id: str) -> Path | None:
        return None

    def _get_out_dir_path(self, case_id: str) -> Path:
        return Path(self.workflow_root, case_id)

    def _get_workflow_version(self, case_config: NextflowCaseConfig) -> str:
        return case_config.revision
