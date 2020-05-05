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
        self.vogue_config = config["vogue"]["config_path"]
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

    def load_bioinfo_raw(self, load_bioinfo_inputs):
        """Running vogue load bioinfo raw."""

        load_bioinfo_raw_call = [
            "--config",
            self.vogue_config,
            "load",
            "bioinfo",
            "raw",
            "--sample-list",
            load_bioinfo_inputs["samples"],
            "--analysis-result",
            load_bioinfo_inputs["analysis_result_file"],
            "--analysis-type",
            load_bioinfo_inputs["analysis_type"],
            "--analysis-case",
            load_bioinfo_inputs["analysis_case_name"],
            "--workflow-version",
            load_bioinfo_inputs["analysis_workflow_version"],
            "--case-analysis-type",
            load_bioinfo_inputs["case_analysis_type"],
            "--analysis-workflow",
            load_bioinfo_inputs["analysis_workflow_name"],
        ]

        self.process.run_command(load_bioinfo_raw_call)

    def load_bioinfo_process(self, load_bioinfo_inputs, cleanup_flag):
        """Running load bioinfo process."""

        load_bioinfo_process_call = [
            "--config",
            self.vogue_config,
            "load",
            "bioinfo",
            "process",
            "--analysis-type",
            load_bioinfo_inputs["analysis_type"],
            "--analysis-case",
            load_bioinfo_inputs["analysis_case_name"],
            "--analysis-workflow",
            load_bioinfo_inputs["analysis_workflow_name"],
            "--workflow-version",
            load_bioinfo_inputs["analysis_workflow_version"],
            "--case-analysis-type",
            load_bioinfo_inputs["case_analysis_type"],
        ]

        if cleanup_flag:
            load_bioinfo_process_call.append("--cleanup")

        self.process.run_command(load_bioinfo_process_call)

    def load_bioinfo_sample(self, load_bioinfo_inputs):
        """Running load bioinfo sample."""

        load_bioinfo_sample_call = [
            "--config",
            self.vogue_config,
            "load",
            "bioinfo",
            "sample",
            "--analysis-case",
            load_bioinfo_inputs["analysis_case_name"],
        ]

        self.process.run_command(load_bioinfo_sample_call)
