# -*- coding: utf-8 -*-

"""
    Module for loqusdb API
"""

import json
import copy
import logging

import subprocess
from subprocess import CalledProcessError

from cg.exc import CaseNotFoundError

LOG = logging.getLogger(__name__)


class LoqusdbAPI:

    """
        API for loqusdb
    """

    def __init__(self, config: dict, analysis_type: str = "wgs"):
        super(LoqusdbAPI, self).__init__()

        self.analysis_type = analysis_type

        self.loqusdb_config = config["loqusdb"]["config_path"]
        self.loqusdb_binary = config["loqusdb"]["binary_path"]

        if self.analysis_type == "wes":
            self.loqusdb_config = config["loqusdb-wes"]["config_path"]
            self.loqusdb_binary = config["loqusdb-wes"]["binary_path"]

        self.base_call = [self.loqusdb_binary, "--config", self.loqusdb_config]

    def load(
        self,
        family_id: str,
        ped_path: str,
        vcf_path: str,
        gbcf_path: str,
        vcf_sv_path=None,
    ) -> dict:
        """Add observations from a VCF."""
        load_call = copy.deepcopy(self.base_call)
        load_call.extend(
            [
                "load",
                "-c",
                family_id,
                "-f",
                ped_path,
                "--variant-file",
                vcf_path,
                "--check-profile",
                gbcf_path,
                "--hard-threshold",
                "0.95",
                "--soft-threshold",
                "0.90",
            ]
        )
        if self.analysis_type == "wgs" and vcf_sv_path:
            load_call.extend(["--sv-variants", vcf_sv_path])

        nr_variants = 0
        # Execute command and print its stdout+stderr as it executes
        for line in execute_command(load_call):
            log_msg = f"loqusdb output: {line}"
            LOG.info(log_msg)
            line_content = line.split("INFO")[-1].strip()
            if "inserted" in line_content:
                nr_variants = int(line_content.split(":")[-1].strip())

        return dict(variants=nr_variants)

    def get_case(self, case_id: str) -> dict:
        """Find a case in the database by case id."""
        case_obj = None
        case_call = copy.deepcopy(self.base_call)

        case_call.extend(["cases", "-c", case_id, "--to-json"])

        try:
            output = subprocess.check_output(" ".join(case_call), shell=True)

        except CalledProcessError:
            # If CalledProcessError is raised, log and raise error
            log_msg = f"Could not run command: {' '.join(case_call)}"
            LOG.critical(log_msg)
            raise

        output = output.decode("utf-8")

        # If case not in loqusdb, stdout of loqusdb command will be empty.
        if not output:
            raise CaseNotFoundError(f"Case {case_id} not found in loqusdb")

        case_obj = json.loads(output)[0]

        return case_obj

    def get_duplicate(self, vcf_file: str) -> dict:
        """Find matching profiles in loqusdb"""
        ind_obj = {}
        ind_call = copy.deepcopy(self.base_call)
        ind_call.extend(
            ["profile", "--check-vcf", vcf_file, "--profile-threshold", "0.95"]
        )

        try:
            output = subprocess.check_output(" ".join(ind_call), shell=True)

        except CalledProcessError:
            # If CalledProcessError is raised, log and raise error
            log_msg = f"Could not run command: {' '.join(ind_call)}"
            LOG.critical(log_msg)
            raise

        output = output.decode("utf-8")

        if not output:
            LOG.info("No duplicates found")
            return ind_obj

        ind_obj = json.loads(output)

        return ind_obj

    def __repr__(self):

        return (
            f"LoqusdbAPI(binary={self.loqusdb_binary}," f"config={self.loqusdb_config})"
        )


def execute_command(cmd):
    """
        Prints stdout + stderr of command in real-time while being executed

        Args:
            cmd (list): command sequence

        Yields:
            line (str): line of output from command
    """
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1
    )

    for line in process.stdout:
        yield line.decode("utf-8").strip()

    def process_failed(process):
        """See if process failed by checking returncode"""
        return process.poll() != 0

    if process_failed(process):
        raise CalledProcessError(returncode=process.returncode, cmd=cmd)
