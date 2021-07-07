"""
    Module for loqusdb API
"""
from pathlib import Path

import json
import logging
from subprocess import CalledProcessError

from cg.exc import CaseNotFoundError
from cg.utils import Process

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
            self.loqusdb_config = config["loqusdb_wes"]["config_path"]
            self.loqusdb_binary = config["loqusdb_wes"]["binary_path"]

        self.process = Process(self.loqusdb_binary, self.loqusdb_config)

    def load(
        self,
        family_id: str,
        ped_path: Path,
        vcf_path: Path,
        gbcf_path: Path,
        vcf_sv_path: Path = None,
    ) -> dict:
        """Add observations from a VCF."""
        load_call_parameters = [
            "load",
            "-c",
            family_id,
            "-f",
            ped_path.as_posix(),
            "--variant-file",
            vcf_path.as_posix(),
            "--check-profile",
            gbcf_path.as_posix(),
            "--hard-threshold",
            "0.95",
            "--soft-threshold",
            "0.90",
        ]
        if self.analysis_type == "wgs" and vcf_sv_path:
            load_call_parameters.extend(["--sv-variants", vcf_sv_path.as_posix()])

        nr_variants = 0
        self.process.run_command(parameters=load_call_parameters)
        for line in self.process.stderr_lines():
            line_content = line.split("INFO")[-1].strip()
            if "inserted" in line_content:
                nr_variants = int(line_content.split(":")[-1].strip())

        return dict(variants=nr_variants)

    def get_case(self, case_id: str) -> dict:
        """Find a case in the database by case id."""
        case_obj = None
        cases_parameters = ["cases", "-c", case_id, "--to-json"]

        self.process.run_command(parameters=cases_parameters)

        output = self.process.stdout

        # If case not in loqusdb, stdout of loqusdb command will be empty.
        if not output:
            raise CaseNotFoundError(f"Case {case_id} not found in loqusdb")

        case_obj = json.loads(output)[0]

        return case_obj

    def get_duplicate(self, vcf_file: Path) -> dict:
        """Find matching profiles in loqusdb"""
        ind_obj = {}
        duplicates_params = [
            "profile",
            "--check-vcf",
            vcf_file.as_posix(),
            "--profile-threshold",
            "0.95",
        ]

        try:
            self.process.run_command(parameters=duplicates_params)
        except CalledProcessError:
            # If CalledProcessError is raised, log and raise error
            LOG.critical("Could not run profile command")
            raise

        output = self.process.stdout

        if not output:
            LOG.info("No duplicates found")
            return ind_obj

        ind_obj = json.loads(output)

        return ind_obj

    def __repr__(self):

        return f"LoqusdbAPI(binary={self.loqusdb_binary}," f"config={self.loqusdb_config})"
