from pathlib import Path

from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.services.analysis_starter.tracker.tracker import Tracker


class MIPDNATracker(Tracker):

    def _workflow_manager(self):
        pass

    def _get_job_ids_path(self, case_id: str) -> Path:
        return Path(self.workflow_root, case_id, "analysis", "slurm_job_ids.yaml")

    def _get_workflow_version(self, case_config: MIPDNACaseConfig) -> str:
        pass
