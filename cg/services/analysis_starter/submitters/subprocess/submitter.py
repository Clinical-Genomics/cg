import logging
import subprocess

from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.services.analysis_starter.submitters.submitter import Submitter
from cg.services.analysis_starter.submitters.subprocess.commands import WORKFLOW_VERSION_COMMAND_MAP

LOG = logging.getLogger(__name__)

SubprocessCaseConfig = MicrosaltCaseConfig


class SubprocessSubmitter(Submitter):
    def submit(self, case_config: SubprocessCaseConfig) -> None:
        command: str = case_config.get_start_command()
        LOG.info(f"Running: {command}")
        subprocess.run(
            args=command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    @staticmethod
    def get_workflow_version(case_config: SubprocessCaseConfig) -> str:
        """
        Calls the workflow to get the workflow version number.
        If fails, returns a placeholder value instead.
        """
        try:
            command: str = WORKFLOW_VERSION_COMMAND_MAP[case_config.workflow]
            command = command.format(case_config.model_dump())
            LOG.debug(f"Running: {command}")
            result: subprocess.CompletedProcess = subprocess.run(
                args=command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout: str = result.stdout.decode("utf-8").rstrip()
            return list(stdout)[0].split()[-1]
        except Exception:
            LOG.warning(f"Could not retrieve {case_config.workflow} workflow version!")
            return "0.0.0"
