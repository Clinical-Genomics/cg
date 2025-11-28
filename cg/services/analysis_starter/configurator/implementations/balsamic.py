import logging
from pathlib import Path
from typing import cast

from cg.constants.priority import SlurmQos
from cg.exc import CaseNotConfiguredError
from cg.meta.workflow.fastq import BalsamicFastqHandler
from cg.models.cg_config import BalsamicConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.file_creators.balsamic_config import (
    BalsamicConfigFileCreator,
)
from cg.services.analysis_starter.configurator.models.balsamic import BalsamicCaseConfig
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class BalsamicConfigurator(Configurator):
    def __init__(
        self,
        config: BalsamicConfig,
        config_file_creator: BalsamicConfigFileCreator,
        fastq_handler: BalsamicFastqHandler,
        store: Store,
    ):
        self.store: Store = store

        self.balsamic_binary: Path = config.binary_path
        self.conda_binary: Path = config.conda_binary
        self.environment: str = config.conda_env
        self.head_job_partition: str = config.head_job_partition
        self.root_dir: Path = config.root
        self.slurm_account: str = config.slurm.account

        self.fastq_handler: BalsamicFastqHandler = fastq_handler
        self.config_file_creator: BalsamicConfigFileCreator = config_file_creator

    def configure(self, case_id: str, **flags) -> BalsamicCaseConfig:
        LOG.info(f"Configuring case {case_id}")
        self.fastq_handler.link_fastq_files(case_id)
        fastq_path: Path = self.fastq_handler.get_fastq_dir(case_id)
        self.config_file_creator.create(case_id=case_id, fastq_path=fastq_path, **flags)
        return self.get_config(case_id=case_id, **flags)

    def get_config(self, case_id: str, **flags) -> BalsamicCaseConfig:
        balsamic_config: BalsamicCaseConfig = BalsamicCaseConfig(
            account=self.slurm_account,
            binary=self.balsamic_binary,
            case_id=case_id,
            conda_binary=self.conda_binary,
            environment=self.environment,
            head_job_partition=self.head_job_partition,
            qos=cast(SlurmQos, self.store.get_case_by_internal_id_strict(case_id).slurm_priority),
            sample_config=self._get_sample_config_path(case_id),
        )
        balsamic_config: BalsamicCaseConfig = self._set_flags(config=balsamic_config, **flags)
        self._ensure_required_config_files_exist(balsamic_config)
        return balsamic_config

    def _get_sample_config_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, f"{case_id}.json")

    def _ensure_required_config_files_exist(self, config: BalsamicCaseConfig) -> None:
        if not config.sample_config.exists():
            raise CaseNotConfiguredError(
                f"Please ensure that the config file {config.sample_config} exists."
            )
