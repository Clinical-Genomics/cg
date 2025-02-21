import logging
from pathlib import Path

from cg.constants import FileExtensions
from cg.io.txt import write_txt
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.abstract_service import Configurator
from cg.services.analysis_starter.configurator.models.raredisease import RarediseaseCaseConfig

LOG = logging.getLogger(__name__)


class RarediseaseConfigurator(Configurator):
    """Configurator for Raredisease analysis."""

    def __init__(self, cg_config: CGConfig):
        super().__init__(cg_config)
        self.root_dir: str = cg_config.raredisease.root
        self.workflow_bin_path: str = cg_config.raredisease.workflow_bin_path
        self.profile: str = cg_config.raredisease.profile
        self.conda_env: str = cg_config.raredisease.conda_env
        self.conda_binary: str = cg_config.raredisease.conda_binary
        self.platform: str = cg_config.raredisease.platform
        self.params: str = cg_config.raredisease.params
        self.workflow_config_path: str = cg_config.raredisease.config
        self.resources: str = cg_config.raredisease.resources
        self.tower_binary_path: str = cg_config.tower_binary_path
        self.tower_workflow: str = cg_config.raredisease.tower_workflow
        self.account: str = cg_config.raredisease.slurm.account
        self.email: str = cg_config.raredisease.slurm.mail_user
        self.compute_env_base: str = cg_config.raredisease.compute_env
        self.revision: str = cg_config.raredisease.revision
        self.nextflow_binary_path: str = cg_config.raredisease.binary_path

    def create_config(self, case_id: str) -> RarediseaseCaseConfig:
        return RarediseaseCaseConfig(
            case_id=case_id,
            case_priority="some_priority",
            workflow="raredisease",
            netxflow_config_file=self._get_nextflow_config_path(case_id=case_id).as_posix(),
            params_file=self._get_params_file_path(case_id=case_id).as_posix(),
            work_dir=Path(self.root_dir, case_id, "work").as_posix(),
        )

    def _create_nextflow_config(self, case_id: str) -> None:
        if content := self._get_nextflow_config_content(case_id=case_id):
            LOG.debug("Writing nextflow config file")
            write_txt(
                content=content,
                file_path=self._get_nextflow_config_path(case_id=case_id),
            )

    def _get_case_path(self, case_id: str) -> Path:
        """Path to case working directory."""
        return Path(self.root_dir, case_id)

    def _get_params_file_path(self, case_id: str) -> Path:
        return Path((self._get_case_path(case_id)), f"{case_id}_params_file").with_suffix(
            FileExtensions.YAML
        )

    def _get_nextflow_config_path(self, case_id: str) -> Path:
        return Path((self._get_case_path(case_id)), f"{case_id}_nextflow_config").with_suffix(
            FileExtensions.JSON
        )
