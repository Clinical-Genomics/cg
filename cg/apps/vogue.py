"""
    Module for vogue API
"""

import json
import logging
from cg.utils.commands import Process

LOG = logging.getLogger(__name__)


class VogueAPI:

    """
        API for vogue
    """

    def __init__(self, config: dict):
        super(VogueAPI, self).__init__()
        self.vogue_binary = config["vogue"]["binary_path"]
        self.process = Process(binary=self.vogue_binary)

    def load_genotype_data(self, genotype_dict: dict):
        """Load genotype data from a dict."""

        load_call = ["load", "genotype", "-s", json.dumps(genotype_dict)]
        self.process.run_command(load_call)

        # Execute command and print its stdout+stderr as it executes
        for line in self.process.stderr_lines():
            LOG.info("vogue output: %s", line)

    def load_apptags(self, apptag_list: list):
        """Add observations from a VCF."""
        load_call = ["load", "apptag", json.dumps(apptag_list)]
        self.process.run_command(load_call)

        # Execute command and print its stdout+stderr as it executes
        for line in self.process.stderr_lines():
            LOG.info("vogue output: %s", line)

    def load_samples(self, days):
        """Running vogue load samples."""

        load_call = ["load", "sample", "-d", days]
        self.process.run_command(load_call)

        # Execute command and print its stdout+stderr as it executes
        for line in self.process.stderr_lines():
            LOG.info("vogue output: %s", line)

    def load_flowcells(self, days):
        """Running vogue load flowcells."""

        load_call = ["load", "flowcell", "-d", days]
        self.process.run_command(load_call)

        # Execute command and print its stdout+stderr as it executes
        for line in self.process.stderr_lines():
            LOG.info("vogue output: %s", line)
