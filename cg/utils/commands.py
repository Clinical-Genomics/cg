"""
Code to handle communications to the shell from CG
"""

import copy
import logging
import subprocess
from subprocess import CalledProcessError

LOG = logging.getLogger(__name__)


class Process(object):
    """Class to handle communication with other programs via the shell

    The other parts of the code should not need to have any knowledge about how the processes are
    called, that will be handled in this module.Output form stdout and stdin will be handeld here.
    """

    def __init__(self, binary, config=None, config_parameter="--config"):
        """
        Args:
            binary(str): Path to binary for the process to use
            config(str): Path to config if used by process
        """
        super(Process, self).__init__()
        self.binary = binary
        LOG.info("Initialising Process with binary: {}".format(self.binary))
        self.base_call = [self.binary]
        if config:
            self.base_call.extend([config_parameter, config])
        LOG.info("Use base call %s", self.base_call)
        self._stdout = ""
        self._stderr = ""

    def run_command(self, parameters=None):
        """Execute a command in the shell

        Args:
            parameters(list)
        """
        command = copy.deepcopy(self.base_call)
        if parameters:
            command.extend(parameters)
        try:
            LOG.info("Running command %s", command)
            res = subprocess.run(
                command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except CalledProcessError as err:
            LOG.warning(err)
            raise err

        self.stdout = res.stdout.decode("utf-8").rstrip()
        self.stderr = res.stdout.decode("utf-8").rstrip()

        return res.returncode

    @property
    def stdout(self):
        return self._stdout

    @stdout.setter
    def stdout(self, text):
        self._stdout = text

    @stdout.deleter
    def stdout(self):
        del self._stdout

    @property
    def stderr(self):
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
