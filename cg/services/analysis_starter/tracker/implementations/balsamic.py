from pathlib import Path

from cg.constants.constants import WorkflowManager
from cg.io.json import read_json
from cg.services.analysis_starter.configurator.models.balsamic import BalsamicCaseConfig
from cg.services.analysis_starter.tracker.tracker import Tracker


class BalsamicTracker(Tracker):

    def _workflow_manager(self):
        return WorkflowManager.Slurm

    def _get_job_ids_path(self, case_id: str) -> Path:
        return Path(self.workflow_root, case_id, "analysis", "slurm_jobids.yaml")

    def _get_workflow_version(self, case_config: BalsamicCaseConfig) -> str:
        config_data: dict = read_json(case_config.sample_config)
        return config_data["analysis"]["BALSAMIC_version"]
