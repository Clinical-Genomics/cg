import logging
import subprocess

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig
from cg.services.analysis_starter.submitters.submitter import Submitter
from cg.services.analysis_starter.submitters.subprocess.commands import WORKFLOW_COMMAND_MAP

LOG = logging.getLogger(__name__)


class SubprocessSubmitter(Submitter):
    def submit(self, case_config: CaseConfig) -> None:
        command: str = self._get_command(case_config)
        LOG.info(f"Running: {command}")
        subprocess.run(
            args=command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    @staticmethod
    def _get_command(case_config: CaseConfig) -> str:
        command: str = WORKFLOW_COMMAND_MAP[case_config.workflow]
        return command.format(**case_config.model_dump())
