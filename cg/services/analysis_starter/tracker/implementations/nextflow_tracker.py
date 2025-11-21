from pathlib import Path

from cg.constants.constants import FileExtensions, WorkflowManager
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.tracker.tracker import Tracker


class NextflowTracker(Tracker):
    def _workflow_manager(self) -> WorkflowManager:
        return WorkflowManager.Tower

    def _get_job_ids_path(self, case_id: str) -> Path:
        """Return the path to a Trailblazer config file containing Tower IDs."""
        return Path(self.workflow_root, case_id, "tower_ids").with_suffix(FileExtensions.YAML)

    def _get_workflow_version(self, case_config: NextflowCaseConfig) -> str:
        return case_config.revision
