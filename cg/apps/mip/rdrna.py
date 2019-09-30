""" Common microsalt related functionality """
import logging
import signal
import subprocess


CLI_OPTIONS = {
    'family': {'option': '--family_id'},
    'config': {'option': '--config_file'},
    'priority': {'option': '--slurm_quality_of_service'},
    'email': {'option': '--email'},
    'base': {'option': '--cluster_constant_path'},
    'dryrun': {
        'option': '--dry_run_all',
        'default': '2',
    },
    'gene_list': {'option': '--vcfparser_select_file'},
    'max_gaussian': {
        'option': '--gatk_variantrecalibration_snv_max_gaussians',
        'default': '1',
    },
    'skip_evaluation': {'option': '--qccollect_skip_evaluation'},
    'start_with': {'option': '--start_with_program'},
}


class MipStartError(Exception):
    """ Throw this when MIP is fussing """


class MipRDRNAAPI():
    """ Group MIP rare disease RNA specific functionality """

    def __init__(self, script, logger=logging.getLogger(__name__)):
        """Initialize MIP command line interface."""
        self.script = script
        self.log = logger

    def __call__(self, config, family, **kwargs):
        """Execute the pipeline."""
        command = self.build_command(config, family=family, **kwargs)
        self.log.debug(' '.join(command))
        process = self.execute(command)
        process.wait()
        if process.returncode != 0:
            raise MipStartError('error starting analysis, check the output')
        return process

    def build_command(self, config, **kwargs):
        """Builds the command to execute MIP."""
        command = ['perl', self.script, CLI_OPTIONS['config']['option'], config]
        for key, value in kwargs.items():
            # enable passing in flags as "False" - shouldn't add command
            if value:
                command.append(CLI_OPTIONS[key]['option'])
                if value is True:
                    command.append(CLI_OPTIONS[key].get('default', '1'))
                else:
                    command.append(value)
        return command

    @classmethod
    def execute(cls, command):
        """Start a new MIP run."""
        process = subprocess.Popen(
            command,
            preexec_fn=lambda: signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        )
        return process
