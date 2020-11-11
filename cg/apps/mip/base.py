""" Common MIP related functionality """

import logging

from cg.constants import SPACE
from cg.utils import Process

LOG = logging.getLogger(__name__)

"""
This dict is built like this:
'cg-option': {
     'option': '--mip-option
}

Defaults can also be set:
'cg-option': {
    'option': '--mip-option',
    'default': '1'
}

This dict is used in `build_command`.

"""
CLI_OPTIONS = {
    "config": {"option": "--config_file"},
    "priority": {"option": "--slurm_quality_of_service"},
    "email": {"option": "--email"},
    "base": {"option": "--cluster_constant_path"},
    "dryrun": {"option": "--dry_run_all"},
    "gene_list": {"option": "--vcfparser_slt_fl"},
    "max_gaussian": {"option": "--gatk_varrecal_snv_max_gau"},
    "skip_evaluation": {"option": "--qccollect_skip_evaluation"},
    "start_with": {"option": "--start_with_recipe"},
}


class MipAPI:
    """ Group MIP specific functionality """

    def __init__(self, script: str, pipeline: str, conda_env: str, **kwargs):
        """Initialize MIP command line interface"""
        self.script = script
        self.pipeline = pipeline
        self.conda_env = conda_env

    def run_command(self, config: str, case: str, dry_run: bool = False, **kwargs) -> None:
        """Execute the workflow"""
        command = self.build_command(config, case, **kwargs)
        self.execute(command, dry_run)

    def build_command(self, config: str, case: str, **kwargs) -> dict:
        """Build the command dict to execute MIP"""
        binary_command = [self.script, self.pipeline, case]
        parameters = []
        for key, value in kwargs.items():
            if value:
                _cg_to_mip_option_map(parameters, key)
                _append_value_for_non_flags(parameters, value)

        command = {
            "binary": SPACE.join(binary_command),
            "config": config,
            "environment": self.conda_env,
            "parameters": parameters,
        }
        return command

    @classmethod
    def execute(cls, command: dict, dry_run: bool = False) -> int:
        """Start a new MIP analysis
        Args:
            command(dict): Command to execute
            dry_run(bool): Print command instead of executing it
        """
        mip_process = Process(
            command["binary"], config=command["config"], environment=command["environment"]
        )

        process_return_code = mip_process.run_command(
            dry_run=dry_run, parameters=command["parameters"]
        )
        for line in mip_process.stdout_lines():
            LOG.info(line)
        for line in mip_process.stderr_lines():
            LOG.info(line)
        return process_return_code


def _append_value_for_non_flags(parameters: list, value) -> None:
    """Add the value of the non boolean options to the parameters"""
    if value is not True:
        parameters.append(value)


def _cg_to_mip_option_map(parameters: list, mip_key) -> None:
    """Map cg options to MIP option syntax"""
    parameters.append(CLI_OPTIONS[mip_key]["option"])
