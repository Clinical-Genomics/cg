import logging
from pathlib import Path

from cg.constants import FileExtensions, Priority, Workflow
from cg.io.txt import concat_txt
from cg.models.cg_config import RarediseaseConfig
from cg.services.analysis_starter.configurator.abstract_service import Configurator
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.configurator.utils import (
    get_slurm_qos_for_case,
    write_content_to_file_or_stdout,
)
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class RarediseaseConfigurator(Configurator):
    """Configurator for Raredisease analysis."""

    def __init__(self, store: Store, config: RarediseaseConfig):
        self.account: str = config.slurm.account
        self.platform: str = config.platform
        self.resources: str = config.resources
        self.root_dir: str = config.root
        self.store: Store = store
        self.workflow_config_path: str = config.config

    def create_config(self, case_id: str, dry_run: bool = False) -> NextflowCaseConfig:
        self._create_case_directory(case_id=case_id, dry_run=False)
        self._create_nextflow_config(case_id=case_id, dry_run=False)
        return NextflowCaseConfig(
            case_id=case_id,
            case_priority=self._get_case_priority(case_id),
            workflow=self._get_case_workflow(case_id),
            netxflow_config_file=self._get_nextflow_config_path(case_id=case_id).as_posix(),
            params_file=self._get_params_file_path(case_id=case_id).as_posix(),
            work_dir=self._get_work_dir(case_id=case_id).as_posix(),
        )

    def _create_case_directory(self, case_id: str, dry_run: bool = False) -> None:
        """Create case working directory."""
        case_path: Path = self._get_case_path(case_id=case_id)
        if dry_run:
            LOG.info(f"Would have created case directory {case_path.as_posix()}")
            return
        case_path.mkdir(parents=True, exist_ok=True)
        LOG.debug(f"Created case directory {case_path.as_posix()} successfully")

    def _create_nextflow_config(self, case_id: str, dry_run: bool = False) -> None:
        """Create nextflow config file."""
        content: str = self._get_nextflow_config_content(case_id=case_id)
        file_path: Path = self._get_nextflow_config_path(case_id=case_id)
        write_content_to_file_or_stdout(content=content, file_path=file_path, dry_run=dry_run)
        LOG.debug(f"Created nextflow config file {file_path.as_posix()} successfully")

    def _get_case_path(self, case_id: str) -> Path:
        """Path to case working directory."""
        return Path(self.root_dir, case_id)

    def _get_case_priority(self, case_id: str) -> Priority:
        return self.store.get_case_by_internal_id(case_id).priority

    def _get_case_workflow(self, case_id: str) -> Workflow:
        case: Case = self.store.get_case_by_internal_id(case_id)
        return Workflow(case.data_analysis)

    def _get_nextflow_config_content(self, case_id: str) -> str:
        config_files_list: list[str] = [
            self.platform,
            self.workflow_config_path,
            self.resources,
        ]
        case_specific_params: list[str] = [
            self._get_cluster_options(case_id=case_id),
        ]
        return concat_txt(
            file_paths=config_files_list,
            str_content=case_specific_params,
        )

    def _get_nextflow_config_path(self, case_id: str) -> Path:
        return Path((self._get_case_path(case_id)), f"{case_id}_nextflow_config").with_suffix(
            FileExtensions.JSON
        )

    def _get_params_file_path(self, case_id: str) -> Path:
        return Path((self._get_case_path(case_id)), f"{case_id}_params_file").with_suffix(
            FileExtensions.YAML
        )

    def _get_work_dir(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "work")

    def _get_cluster_options(self, case_id: str) -> str:
        case: Case = self.store.get_case_by_internal_id(case_id)
        qos: str = get_slurm_qos_for_case(case)
        return f'process.clusterOptions = "-A {self.account} --qos={qos}"\n'
