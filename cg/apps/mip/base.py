""" Common MIP related functionality """

from cg.constants import SINGLE_QUOTE, SPACE
from cg.utils import Process

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


class MipStartError(Exception):
    """ Catch this when MIP throws an error """


class MipAPI:
    """ Group MIP specific functionality """

    def __init__(self, script: str, pipeline: str, conda_env: str):
        """Initialize MIP command line interface"""
        self.script = script
        self.pipeline = pipeline
        self.conda_env = conda_env

    def run(self, config: str, case: str, dry_run: bool = False, **kwargs) -> None:
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
    def execute(self, mip_process: Process, command: dict, dry_run: bool = False) -> None:
        """Start a new MIP analysis
        Args:
            command(list): Command to execute
            dry_run: Print command instead of executing it
        """

        process_returncode = mip_process.run_command(
            dry_run,
            binary=command[binary],
            config=command[config],
            environment=command[environment],
            parameters=command[parameters],
        )
        success = 0
        if process_returncode != success:
            raise MipStartError("error running analysis, check the output")


def _append_value_for_non_flags(parameters: list, value):
    """Add the value of the non boolean options to the parameters"""
    if value is not True:
        parameters.append(value)


def _cg_to_mip_option_map(parameters: list, mip_key):
    """Map cg options to MIP option syntax"""
    parameters.append(CLI_OPTIONS[mip_key]["option"])
