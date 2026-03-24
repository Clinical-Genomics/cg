import logging
import subprocess

from cg.constants import EXIT_SUCCESS
from cg.exc import WorkflowVersionCommandFailedError
from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.services.analysis_starter.submitters.submitter import Submitter
from cg.services.analysis_starter.submitters.subprocess.commands import WORKFLOW_VERSION_COMMAND_MAP

LOG = logging.getLogger(__name__)

SubprocessCaseConfig = MicrosaltCaseConfig | MIPDNACaseConfig


class SubprocessSubmitter(Submitter):
    def submit(self, case_config: SubprocessCaseConfig) -> SubprocessCaseConfig:
        command: str = case_config.get_start_command()
        LOG.info(f"Running: {command}")
        subprocess.run(
            args=command,
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return case_config

    @staticmethod
    def get_workflow_version(case_config: SubprocessCaseConfig) -> str:
        """
        Calls the workflow to get the workflow version number.
        If fails, returns a placeholder value instead.

        Currently supported workflow: microSALT
        """
        try:
            command: str = WORKFLOW_VERSION_COMMAND_MAP[case_config.workflow]
            command = command.format(**case_config.model_dump())
            LOG.debug(f"Running: {command}")
            result: subprocess.CompletedProcess = subprocess.run(
                args=command,
                shell=True,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            if result.returncode != EXIT_SUCCESS:
                stderr: str = result.stderr.decode("utf-8").rstrip()
                raise WorkflowVersionCommandFailedError(f"Exit code {result.returncode}: {stderr}")

            stdout: str = result.stdout.decode("utf-8").rstrip()
            return stdout.split()[-1]

        except Exception as e:
            LOG.warning(f"Could not retrieve {case_config.workflow} workflow version: {e}")
            return "0.0.0"
