"""
    Module for vogue API
"""

import json
import logging

import subprocess
from subprocess import CalledProcessError

LOG = logging.getLogger(__name__)


class VogueAPI():

    """
        API for vogue
    """

    def __init__(self, config: dict):
        super(VogueAPI, self).__init__()
        self.vogue_binary = config['vogue']['binary_path']
        self.base_call = [self.vogue_binary]

    def load_genotype(self, genotype_dict: dict):
        """Add observations from a VCF."""
        load_call = self.base_call[:]
        load_call.extend(['load', 'genotype', '-s', json.dumps(genotype_dict)])

        # Execute command and print its stdout+stderr as it executes
        for line in execute_command(load_call):
            log_msg = f"vogue output: {line}"
            LOG.info(log_msg)


def execute_command(cmd):
    """
        Prints stdout + stderr of command in real-time while being executed

        Args:
            cmd (list): command sequence

        Yields:
            line (str): line of output from command
    """
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               bufsize=1)

    for line in process.stdout:
        yield line.decode('utf-8').strip()

    # Check if process exited with returncode != 0
    if process.poll():
        raise CalledProcessError(returncode=process.returncode, cmd=cmd)
