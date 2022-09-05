"""
    Module for loqusdb API
"""
import logging
from pathlib import Path
from subprocess import CalledProcessError

from cg.constants.constants import FileFormat
from cg.exc import CaseNotFoundError
from cg.io.controller import ReadStream
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
            "--gq-treshold",
            "10",
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
        """Find a case in the database by case id"""
        cases_parameters = ["cases", "-c", case_id, "--to-json"]

        self.process.run_command(parameters=cases_parameters)

        # If case not in loqusdb, stdout of loqusdb command will be empty.
        if not self.process.stdout:
            raise CaseNotFoundError(f"Case {case_id} not found in loqusdb")

        return ReadStream.get_content_from_stream(
            file_format=FileFormat.JSON, stream=self.process.stdout
        )[0]

    def get_duplicate(self, vcf_file: Path) -> dict:
        """Find matching profiles in loqusdb"""
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

        if not self.process.stdout:
            LOG.info("No duplicates found")
            return {}

        return ReadStream.get_content_from_stream(
            file_format=FileFormat.JSON, stream=self.process.stdout
        )

    def __repr__(self):

        return f"LoqusdbAPI(binary={self.loqusdb_binary}," f"config={self.loqusdb_config})"
