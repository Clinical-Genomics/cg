# -*- coding: utf-8 -*-

"""
    Module for vogue API
"""

import json
import copy
import logging

import subprocess
from subprocess import CalledProcessError

from cg.exc import CaseNotFoundError

LOG = logging.getLogger(__name__)


class VogueAPI():

    """
        API for vogue
    """

    def __init__(self, config: dict):
        super(VogueAPI, self).__init__()
        self.vogue_binary = config['vogue']['binary_path']
        self.base_call = [self.vogue_binary]

    def load_genotype(self, genotype_dict: dict ):
        """Add observations from a VCF."""
        load_call = copy.deepcopy(self.base_call)
        load_call.extend(['load', 'genotype', '-s', genotype_dict])

        # Execute command and print its stdout+stderr as it executes
        for line in execute_command(load_call):
            log_msg = f"vogue output: {line}"
            LOG.info(log_msg)
            line_content = line.split('INFO')[-1].strip()
 