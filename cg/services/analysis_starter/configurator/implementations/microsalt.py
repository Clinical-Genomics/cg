import logging
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.exc import MissingConfigFilesError
from cg.meta.workflow.fastq import MicrosaltFastqHandler
from cg.models.cg_config import MicrosaltConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)
from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class MicrosaltConfigurator(Configurator):
    def __init__(
        self,
        config_file_creator: MicrosaltConfigFileCreator,
        fastq_handler: MicrosaltFastqHandler,
        lims_api: LimsAPI,
        microsalt_config: MicrosaltConfig,
        store: Store,
    ):
        self.config_file_creator = config_file_creator
        self.fastq_handler = fastq_handler
        self.lims_api = lims_api
        self.config = microsalt_config
        self.store = store

    def configure(self, case_id: str, **flags) -> MicrosaltCaseConfig:
        LOG.info(f"Configuring case {case_id}")
        self.fastq_handler.link_fastq_files(case_id)
        self.config_file_creator.create(case_id)
        return self.get_config(case_id=case_id, **flags)

    def get_config(self, case_id: str, **flags) -> MicrosaltCaseConfig:
        config_file_path: Path = flags.get(
            "config_path", self.config_file_creator.get_config_path(case_id)
        )
        fastq_directory: Path = self._get_fastq_directory(case_id)
        config = MicrosaltCaseConfig(
            binary=self.config.binary_path,
            case_id=case_id,
            conda_binary=self.config.conda_binary,
            config_file=config_file_path.as_posix(),
            environment=self.config.conda_env,
            fastq_directory=fastq_directory.as_posix(),
        )
        config: MicrosaltCaseConfig = self._set_flags(config=config, **flags)
        self._ensure_required_config_files_exist(config)
        return config

    def _get_fastq_directory(self, case_id: str) -> Path:
        """
        Returns the directory in which the pipeline will look for Fastq files
        depending on whether the case has one or multiple samples.
        """
        case: Case = self.store.get_case_by_internal_id(case_id)
        if len(case.samples) == 1:
            LOG.debug(
                f"Case {case_id} contains only a single sample, so the nested fastq directory for"
                f"{case.samples[0].internal_id} will be used."
            )
            return self.fastq_handler.get_sample_fastq_destination_dir(
                case=case, sample=case.samples[0]
            )
        return self.fastq_handler.get_case_fastq_path(case_id)

    def _ensure_required_config_files_exist(self, config: MicrosaltCaseConfig) -> None:
        """Ensures that a Microsalt config file exists for the case.
        Raises:
            MissingConfigFilesError if the config file does not exist.
        """
        config_file_path = Path(config.config_file)
        if not config_file_path.exists():
            raise MissingConfigFilesError(
                f"Please ensure that the config file {config_file_path.as_posix} exists."
            )
