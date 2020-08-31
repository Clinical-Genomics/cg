"""
    Module for nipt API
"""

import json
import logging
from cg.utils.commands import Process

LOG = logging.getLogger(__name__)


class NiptAPI:

    """
    API for nipt
    """

    def __init__(self, config: dict):
        super(NiptAPI, self).__init__()
        self.nipt_config = config["nipt"]["config_path"]
        self.nipt_binary = config["nipt"]["binary_path"]
        self.process = Process(binary=self.nipt_binary, config=self.nipt_config)

    def load_batch(self, batch_dict: dict):
        """Load nipt batch data from a dict."""

        load_call = ["load", "genotype", "-s", json.dumps(batch_dict)]
        self.process.run_command(parameters=load_call)

        # Execute command and print its stdout+stderr as it executes
        for line in self.process.stderr_lines():
            LOG.info("nipt output: %s", line)
