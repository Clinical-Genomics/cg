import logging
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.constants.constants import Workflow
from cg.meta.workflow.fastq import MicrosaltFastqHandler
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)
from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class MicrosaltConfigurator(Configurator):
    def __init__(
        self,
        config_file_creator: MicrosaltConfigFileCreator,
        fastq_handler: MicrosaltFastqHandler,
        lims_api: LimsAPI,
        store: Store,
    ):
        self.config_file_creator = config_file_creator
        self.fastq_handler = fastq_handler
        self.lims_api = lims_api
        self.store = store

    def configure(self, case_id: str) -> MicrosaltCaseConfig:
        self.fastq_handler.link_fastq_files(case_id)
        self.config_file_creator.create(case_id)
        return self.get_config(case_id)

    def get_config(self, case_id: str) -> MicrosaltCaseConfig:
        config_file_path: Path = self.config_file_creator.get_config_path(case_id)
        return MicrosaltCaseConfig(
            case_id=case_id, config_file_path=config_file_path, workflow=Workflow.MICROSALT
        )
