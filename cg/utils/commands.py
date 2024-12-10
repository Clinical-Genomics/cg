"""
Code to handle communications to the shell from CG.
"""

import copy
import logging
import subprocess
from subprocess import CalledProcessError

from cg.constants.process import EXIT_SUCCESS

LOG = logging.getLogger(__name__)


class Process:
    """Class to handle communication with other programs via the shell.

    The other parts of the code should not need to have any knowledge about how the processes are
    called; that will be handled in this module.Output form stdout and stdin will be handled here.
    """

    def __init__(
        self,
        binary: str,
        conda_binary: str = None,
        config: str = None,
        config_parameter: str = "--config",
        environment: str = None,
        launch_directory: str = None,
    ):
        """
        Args:
            binary(str): Path to binary for the process to use
            config(str): Path to config if used by process
            environment(str): Activate conda environment before executing binary
        """
        super(Process, self).__init__()
        self.binary: str = binary
        self.conda_binary: str = conda_binary
        self.config: str = config
        self.environment: str = environment
        self.launch_directory: str = launch_directory
        LOG.debug("Initialising Process with binary: %s", self.binary)
        self.base_call: list[str] = [self.binary]

        if conda_binary:
            LOG.debug(f"Activating environment with conda run for binary: {self.conda_binary}")
            self.base_call.insert(0, f"{self.conda_binary} run --name {self.environment}")
        elif environment:
            LOG.debug(f"Activating environment with: {self.environment}")
            self.base_call.insert(0, f"source activate {self.environment};")
        if config:
            self.base_call.extend([config_parameter, config])
        if launch_directory:
            self.base_call.insert(0, f"cd {self.launch_directory};")

        LOG.debug(f"Use base call {self.base_call}")
        self._stdout = ""
        self._stderr = ""

    def export_variables(self, export: dict[str, str]) -> None:
        """Export variables prior to execution."""
        if export:
            self.base_call.insert(
                0, " ".join([f"export {variable}={value};" for variable, value in export.items()])
            )

    def run_command(self, parameters: list = None, dry_run: bool = False) -> int:
        """Execute a command in the shell.
        If environment is supplied - shell=True has to be supplied to enable passing as a string for executing multiple
         commands

        Args:
            parameters(list):
            dry_run(bool): Print command instead of executing it
        Return(int): Return code from called process

        """
        command = copy.deepcopy(self.base_call)
        if parameters:
            command.extend(parameters)

        LOG.info("Running command %s", " ".join(command))
        if dry_run:
            LOG.info("Dry run: process call will not be executed!!")
            return EXIT_SUCCESS

        if self.environment:
            res = subprocess.run(
                " ".join(command),
                shell=True,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        else:
            res = subprocess.run(
                command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

        self.stdout = res.stdout.decode("utf-8").rstrip()
        self.stderr = res.stderr.decode("utf-8").rstrip()
        if res.returncode != EXIT_SUCCESS:
            LOG.critical("Call %s exit with a non zero exit code", command)
            LOG.critical(self.stderr)
            raise CalledProcessError(res.returncode, command)

        return res.returncode

    def get_command(self, parameters: list = None) -> str:
        """Returns a command string given a list of parameters."""

        command: list[str] = copy.deepcopy(self.base_call)
        if parameters:
            command.extend(parameters)

        return " ".join(command)

    @property
    def stdout(self):
        """Fetch stdout"""
        return self._stdout

    @stdout.setter
    def stdout(self, text):
        self._stdout = text

    @stdout.deleter
    def stdout(self):
        del self._stdout

    @property
    def stderr(self):
        """Fetch stderr"""
        return self._stderr

    @stderr.setter
    def stderr(self, text):
        self._stderr = text

    @stderr.deleter
    def stderr(self):
        del self._stderr

    def stdout_lines(self):
        """Iterate over the lines in self.stdout"""
        yield from self.stdout.split("\n")

    def stderr_lines(self):
        """Iterate over the lines in self.stderr"""
        yield from self.stderr.split("\n")

    def __repr__(self):
        return f"Process:base_call:{self.base_call}"
