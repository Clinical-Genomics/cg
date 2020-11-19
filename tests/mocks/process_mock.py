"""Mock a Process"""

from typing import List
import copy
import logging
from subprocess import CalledProcessError

from cg.constants import RETURN_SUCCESS

LOG = logging.getLogger(__name__)


class ProcessMock:
    """Mock the utils.commands.Process class"""

    def __init__(
        self,
        binary: str = None,
        config: str = None,
        config_parameter: str = "--config",
        environment: str = None,
    ):
        """
        Args:
            binary(str): Path to binary for the process to use
            config(str): Path to config if used by process
            environment(str): Activate conda environment before executing binary
        """
        self.binary = binary
        self.config = config
        self.environment = environment
        self.config_parameter = config_parameter
        LOG.debug("Initialising Process with binary: %s", self.binary)
        self.base_call: List = []
        if self.binary:
            self.base_call.append(self.binary)
            if self.environment:
                LOG.debug("Activating environment with: %s", self.environment)
                self.base_call.insert(0, f"source activate {self.environment};")
            if self.config:
                self.base_call.extend([self.config_parameter, self.config])
            LOG.debug("Use base call %s", self.base_call)
        self._stdout = ""
        self._stderr = ""
        self._exit_code: int = RETURN_SUCCESS

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
            return RETURN_SUCCESS

        if self._exit_code != RETURN_SUCCESS:
            LOG.critical("Call %s exit with a non zero exit code", command)
            LOG.critical(self.stderr)
            raise CalledProcessError(self._exit_code, command)

        return RETURN_SUCCESS

    def set_stdout(self, text: str):
        """Mock the stdout"""
        self._stdout = text

    def set_stderr(self, text: str):
        """Mock the stderr"""
        self._stderr = text

    def set_exit_code(self, code: int):
        """Mock the stderr"""
        self._exit_code = code

    def set_binary(self, binary_path: str):
        """Set the binary path"""
        self.binary = binary_path
        self.base_call.append(self.binary)
        if self.environment:
            LOG.debug("Activating environment with: %s", self.environment)
            self.base_call.insert(0, f"source activate {self.environment};")
        if self.config:
            self.base_call.extend([self.config_parameter, self.config])
        LOG.debug("Use base call %s", self.base_call)

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
        for line in self.stdout.split("\n"):
            yield line

    def stderr_lines(self):
        """Iterate over the lines in self.stderr"""
        for line in self.stderr.split("\n"):
            yield line

    def __repr__(self):
        return f"Process:base_call:{self.base_call}"
