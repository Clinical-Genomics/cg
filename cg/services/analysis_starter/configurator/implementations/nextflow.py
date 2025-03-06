from abc import abstractmethod
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.constants import Workflow
from cg.constants.nf_analysis import NextflowFileType
from cg.services.analysis_starter.configurator.abstract_service import Configurator
from cg.services.analysis_starter.configurator.file_creators.config_file import (
    NextflowConfigFileContentCreator,
)
from cg.services.analysis_starter.configurator.file_creators.utils import create_file, get_file_path
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.store.models import Case
from cg.store.store import Store


class NextflowConfigurator(Configurator):

    def __init__(
        self,
        config: any,
        store: Store,
        housekeeper_api: HousekeeperAPI,
        lims: LimsAPI,
        config_content_creator: NextflowConfigFileContentCreator,
    ):
        self.root_dir: str = config.root_dir
        self.store: Store = store
        self.housekeeper_api: HousekeeperAPI = housekeeper_api
        self.lims: LimsAPI = lims
        self.config_content_creator = config_content_creator

    def create_config(self, case_id: str) -> NextflowCaseConfig:
        """Create a Nextflow case config."""
        self._create_case_directory(case_id=case_id)
        self._create_sample_sheet(case_id=case_id)
        self._create_params_file(case_id=case_id)
        self._create_nextflow_config(case_id=case_id)
        self._do_pipeline_specific_actions(case_id=case_id)
        return NextflowCaseConfig(
            case_id=case_id,
            case_priority=self._get_case_priority(case_id),
            workflow=self._get_case_workflow(case_id),
            netxflow_config_file=self._get_nextflow_config_path(case_id=case_id).as_posix(),
            params_file=self._get_params_file_path(case_id=case_id).as_posix(),
            work_dir=self._get_work_dir(case_id=case_id).as_posix(),
        )

    def _create_case_directory(self, case_id: str) -> None:
        """Create case working directory."""
        case_path: Path = self._get_case_path(case_id=case_id)
        case_path.mkdir(parents=True, exist_ok=True)

    def _get_case_path(self, case_id: str) -> Path:
        """Path to case working directory."""
        return Path(self.root_dir, case_id)

    def _create_sample_sheet(self, case_id: str) -> None:
        """Create sample sheet for case."""
        create_file(
            content_creator=self.sample_sheet_content_creator,
            case_path=self._get_case_path(case_id=case_id),
            file_type=NextflowFileType.SAMPLE_SHEET,
        )

    def _create_params_file(self, case_id: str) -> None:
        """Create parameters file for case."""
        create_file(
            content_creator=self.params_file_content_creator,
            case_path=self._get_case_path(case_id=case_id),
            file_type=NextflowFileType.PARAMS,
        )

    def _create_nextflow_config(self, case_id: str) -> None:
        """Create nextflow config file for case."""
        create_file(
            content_creator=self.config_content_creator,
            case_path=self._get_case_path(case_id=case_id),
            file_type=NextflowFileType.CONFIG,
        )

    @abstractmethod
    def _do_pipeline_specific_actions(self, case_id: str) -> None:
        """Perform pipeline specific actions."""
        pass

    def _get_case_priority(self, case_id: str) -> str:
        """Get case priority."""
        case: Case = self.store.get_case_by_internal_id(case_id)
        return case.slurm_priority

    def _get_case_workflow(self, case_id: str) -> Workflow:
        """Get case workflow."""
        case: Case = self.store.get_case_by_internal_id(case_id)
        return Workflow(case.data_analysis)

    def _get_nextflow_config_path(self, case_id: str) -> Path:
        case_path: Path = self._get_case_path(case_id)
        return get_file_path(case_path=case_path, file_type=NextflowFileType.CONFIG)

    def _get_params_file_path(self, case_id: str) -> Path:
        case_path: Path = self._get_case_path(case_id)
        return get_file_path(case_path=case_path, file_type=NextflowFileType.PARAMS)

    def _get_work_dir(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "work")
