from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.constants import Workflow
from cg.services.analysis_starter.configurator.abstract_service import Configurator
from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.file_creators.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.sample_sheet.abstract import (
    NextflowSampleSheetCreator,
)
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
        config_file_creator: NextflowConfigFileCreator,
        sample_sheet_creator: NextflowSampleSheetCreator,
        params_file_creator: ParamsFileCreator,
        pipeline_extension: PipelineExtension = PipelineExtension(),
    ):
        self.root_dir: str = config.root
        self.store: Store = store
        self.housekeeper_api: HousekeeperAPI = housekeeper_api
        self.lims: LimsAPI = lims
        self.config_file_creator = config_file_creator
        self.pipeline_extension = pipeline_extension
        self.sample_sheet_creator = sample_sheet_creator
        self.params_file_creator = params_file_creator

    def create_config(self, case_id: str) -> NextflowCaseConfig:
        """Create a Nextflow case config."""
        case_path: Path = self._get_case_path(case_id=case_id)
        self._create_case_directory(case_id=case_id)
        sample_sheet_path: Path = self.sample_sheet_creator.get_file_path(
            case_id=case_id, case_path=case_path
        )
        self.sample_sheet_creator.create(case_id=case_id, case_path=case_path)
        self.params_file_creator.create(
            case_id=case_id, case_path=case_path, sample_sheet_path=sample_sheet_path
        )
        self.config_file_creator.create(case_id=case_id, case_path=case_path)
        config_file_path: Path = self.config_file_creator.get_file_path(
            case_id=case_id, case_path=case_path
        )
        params_file_path: Path = self.params_file_creator.get_file_path(
            case_id=case_id, case_path=case_path
        )
        self.pipeline_extension.configure(case_path)
        return NextflowCaseConfig(
            case_id=case_id,
            case_priority=self._get_case_priority(case_id),
            workflow=self._get_case_workflow(case_id),
            netxflow_config_file=config_file_path.as_posix(),
            params_file=params_file_path.as_posix(),
            work_dir=self._get_work_dir(case_id=case_id).as_posix(),
        )

    def _get_case_path(self, case_id: str) -> Path:
        """Path to case working directory."""
        return Path(self.root_dir, case_id)

    def _create_case_directory(self, case_id: str) -> None:
        """Create case working directory."""
        case_path: Path = self._get_case_path(case_id=case_id)
        case_path.mkdir(parents=True, exist_ok=True)

    def _get_case_priority(self, case_id: str) -> str:
        """Get case priority."""
        case: Case = self.store.get_case_by_internal_id(case_id)
        return case.slurm_priority

    def _get_case_workflow(self, case_id: str) -> Workflow:
        """Get case workflow."""
        case: Case = self.store.get_case_by_internal_id(case_id)
        return Workflow(case.data_analysis)

    def _get_work_dir(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "work")
