from pathlib import Path

from cg.constants.constants import WorkflowManager
from cg.io.yaml import read_yaml
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.services.analysis_starter.tracker.tracker import Tracker


class MIPDNATracker(Tracker):

    def _workflow_manager(self) -> WorkflowManager:
        return WorkflowManager.Slurm

    def _get_job_ids_path(self, case_id: str) -> Path:
        return Path(self.workflow_root, case_id, "analysis", "slurm_job_ids.yaml")

    def _get_sample_info_path(self, case_id: str) -> Path:
        return Path(self.workflow_root, case_id, "analysis", f"{case_id}_qc_sample_info.yaml")

    def _get_workflow_version(self, case_config: MIPDNACaseConfig) -> str:
        sample_info_raw: dict = read_yaml(file_path=self._get_sample_info_path(case_config.case_id))
        return sample_info_raw["mip_version"]
