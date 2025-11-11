from pathlib import Path

from cg.exc import MissingConfigFilesError
from cg.models.cg_config import CommonAppConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.protocol import (
    SampleSheetCreator,
)
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.store.store import Store


class NextflowConfigurator(Configurator):
    def __init__(
        self,
        config_file_creator: NextflowConfigFileCreator,
        params_file_creator: ParamsFileCreator,
        pipeline_config: CommonAppConfig,
        sample_sheet_creator: SampleSheetCreator,
        store: Store,
        pipeline_extension: PipelineExtension = PipelineExtension(),
    ):
        self.root_dir: str = pipeline_config.root
        self.pipeline_repository = pipeline_config.repository
        self.pipeline_revision = pipeline_config.revision
        self.config_profiles = [pipeline_config.profile]
        self.pre_run_script = pipeline_config.pre_run_script
        self.store: Store = store
        self.config_file_creator = config_file_creator
        self.pipeline_extension = pipeline_extension
        self.sample_sheet_creator = sample_sheet_creator
        self.params_file_creator = params_file_creator

    def configure(self, case_id: str, **flags) -> NextflowCaseConfig:
        """Configure a Nextflow case so that it is ready for analysis. This entails
        1. Creating a case directory.
        2. Creating a sample sheet.
        3. Creating a parameters file.
        4. Creating a configuration file.
        5. Creating any pipeline specific files."""
        case_run_directory: Path = self._get_case_run_directory(case_id)
        sample_sheet_path: Path = self._get_sample_sheet_path(case_id)
        params_file_path: Path = self._get_params_file_path(case_id)
        config_file_path: Path = self._get_config_file_path(case_id)

        self._create_case_directory(case_id)
        self.sample_sheet_creator.create(case_id=case_id, file_path=sample_sheet_path)
        self.params_file_creator.create(
            case_id=case_id,
            file_path=params_file_path,
            sample_sheet_path=sample_sheet_path,
        )
        self.config_file_creator.create(case_id=case_id, file_path=config_file_path)
        self.pipeline_extension.configure(case_id=case_id, case_run_directory=case_run_directory)
        return self.get_config(case_id=case_id, **flags)

    def get_config(self, case_id: str, **flags) -> NextflowCaseConfig:
        """
        Gets the configuration properties for the provided case.
        Raises:
            CaseNotConfiguredError if the params file or config file does not exist.
        """
        params_file_path: Path = self._get_params_file_path(case_id=case_id)
        config_file_path: Path = self._get_config_file_path(case_id=case_id)
        config = NextflowCaseConfig(
            case_id=case_id,
            case_priority=self.store.get_case_priority(case_id),
            config_profiles=self.config_profiles,
            nextflow_config_file=config_file_path.as_posix(),
            params_file=params_file_path.as_posix(),
            pipeline_repository=self.pipeline_repository,
            pre_run_script=self.pre_run_script,
            revision=self.pipeline_revision,
            work_dir=self._get_work_dir(case_id).as_posix(),
            workflow=self.store.get_case_workflow(case_id),
        )
        config: NextflowCaseConfig = self._set_flags(config=config, **flags)
        self._ensure_required_config_files_exist(config)
        return config

    def _get_config_file_path(self, case_id: str) -> Path:
        """Return the path to the Nextflow config file."""
        return Path(self._get_case_run_directory(case_id), f"{case_id}_nextflow_config.json")

    def _get_params_file_path(self, case_id: str) -> Path:
        """Return the path to the params file for a case."""
        return Path(self._get_case_run_directory(case_id), f"{case_id}_params_file.yaml")

    def _get_sample_sheet_path(self, case_id: str) -> Path:
        return Path(self._get_case_run_directory(case_id), f"{case_id}_samplesheet.csv")

    def _get_case_run_directory(self, case_id: str) -> Path:
        """Path to case working directory."""
        return Path(self.root_dir, case_id)

    def _create_case_directory(self, case_id: str) -> None:
        """Create case working directory."""
        case_path: Path = self._get_case_run_directory(case_id=case_id)
        case_path.mkdir(parents=True, exist_ok=True)

    def _get_work_dir(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "work")

    def _ensure_required_config_files_exist(self, config: NextflowCaseConfig) -> None:
        """
        Ensure that the config and the params files exists.
        Raises:
            MissingConfigFilesError if either the params file or the config file is missing.
        """
        params_file_path = Path(config.params_file)
        config_file_path = Path(config.nextflow_config_file)
        samplesheet_file_path: Path = self._get_sample_sheet_path(config.case_id)
        if not (
            self.pipeline_extension.do_required_files_exist(
                case_run_directory=self._get_case_run_directory(config.case_id)
            )
            and params_file_path.exists()
            and config_file_path.exists()
            and samplesheet_file_path.exists()
        ):
            raise MissingConfigFilesError(
                f"Please ensure that the parameters file {params_file_path.as_posix()}, "
                f"the configuration file {config_file_path.as_posix()}, "
                f"the sample sheet {samplesheet_file_path.as_posix()}, and "
                f"all pipeline specific files exists."
            )
