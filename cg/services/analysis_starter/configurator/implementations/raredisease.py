import logging
from pathlib import Path

from cg.constants import FileExtensions, Priority, Workflow
from cg.models.cg_config import RarediseaseConfig
from cg.services.analysis_starter.configurator.abstract_service import Configurator
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class RarediseaseConfigurator(Configurator):
    """Configurator for Raredisease analysis."""

    def __init__(self, store: Store, config: RarediseaseConfig):
        super().__init__(store)
        self.root_dir: str = config.root

    def create_config(self, case_id: str) -> NextflowCaseConfig:
        return NextflowCaseConfig(
            case_id=case_id,
            case_priority=self._get_case_priority(case_id),
            workflow=self._get_case_workflow(case_id),
            nextflow_config_file=self._get_nextflow_config_path(case_id=case_id).as_posix(),
            params_file=self._get_params_file_path(case_id=case_id).as_posix(),
            work_dir=self._get_work_dir(case_id=case_id).as_posix(),
        )

    def _create_nextflow_config(self, case_id: str) -> None:
        pass

    def _get_case_path(self, case_id: str) -> Path:
        """Path to case working directory."""
        return Path(self.root_dir, case_id)

    def _get_case_priority(self, case_id: str) -> Priority:
        return self.store.get_case_by_internal_id(case_id).priority

    def _get_case_workflow(self, case_id: str) -> Workflow:
        case: Case = self.store.get_case_by_internal_id(case_id)
        return Workflow(case.data_analysis)

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
