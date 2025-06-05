import logging
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.exc import CaseNotConfiguredError
from cg.meta.workflow.fastq import MicrosaltFastqHandler
from cg.models.cg_config import MicrosaltConfig
from cg.services.analysis_starter.configurator.abstract_model import RunParameters
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)
from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class MicrosaltRunParameters(RunParameters):
    config_path: Path | None = None


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
        overridden_parameters = MicrosaltRunParameters.model_validate(flags)
        config_file_path: Path = (
            overridden_parameters.config_path or self.config_file_creator.get_config_path(case_id)
        )
        if not config_file_path.exists():
            raise CaseNotConfiguredError(
                f"Please ensure that the config file {config_file_path.as_posix} exists."
            )
        fastq_directory: Path = self.fastq_handler.get_case_fastq_path(case_id)
        config = MicrosaltCaseConfig(
            binary=self.config.binary_path,
            case_id=case_id,
            conda_binary=self.config.conda_binary,
            config_file=config_file_path.as_posix(),
            environment=self.config.conda_env,
            fastq_directory=fastq_directory.as_posix(),
        )
        return config.model_copy(update=flags)
