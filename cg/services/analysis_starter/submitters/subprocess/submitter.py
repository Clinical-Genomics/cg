import subprocess

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig
from cg.services.analysis_starter.submitters.submitter import Submitter
from cg.services.analysis_starter.submitters.subprocess.commands import WORKFLOW_COMMAND_MAP


class SubprocessSubmitter(Submitter):
    def submit(self, case_config: CaseConfig):
        command: str = self._get_command(case_config)
        subprocess.run(
            args=command,
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    @staticmethod
    def _get_command(case_config: CaseConfig) -> str:
        command: str = WORKFLOW_COMMAND_MAP[case_config.workflow]
        return command.format(**case_config.model_dump())
