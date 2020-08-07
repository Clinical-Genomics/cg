""" Common MIP related functionality """
import logging
import subprocess

from cg.constants import SINGLE_QUOTE, SPACE

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
    """ Throw this when MIP is fussing """


class MipAPI:
    """ Group MIP specific functionality """

    def __init__(self, script, pipeline, conda_env, logger=logging.getLogger(__name__)):
        """Initialize MIP command line interface."""
        self.script = script
        self.pipeline = pipeline
        self.conda_env = conda_env
        self.logger = logger

    def run(self, config, case, **kwargs):
        """Execute the workflow"""
        command = self.build_command(config, case, **kwargs)
        self.logger.debug(SPACE.join(command))
        process = self.execute(command)
        success = 0
        if process.returncode != success:
            raise MipStartError("error running analysis, check the output")
        return process

    def build_command(self, config, case, **kwargs):
        """Builds the command to execute MIP"""
        command = [
            f"bash -c 'source activate {self.conda_env};",
            self.script,
            self.pipeline,
            case,
            CLI_OPTIONS["config"]["option"],
            config,
        ]
        for key, value in kwargs.items():
            if value:
                # Cg to mip options mapping
                command.append(CLI_OPTIONS[key]["option"])
                # append value for non-flags
                if value is not True:
                    command.append(value)
        command.append(SINGLE_QUOTE)
        return command

    @classmethod
    def execute(cls, command: str):
        """Start a new MIP run
        Args:
            command(str): Command to execute
        """

        process = subprocess.run(SPACE.join(command), shell=True, check=True)
        return process
