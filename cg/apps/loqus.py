"""Module for Loqusdb API."""

import logging
from pathlib import Path
from subprocess import CalledProcessError

from cg.constants.constants import FileFormat
from cg.exc import CaseNotFoundError, LoqusdbDeleteCaseError
from cg.io.controller import ReadStream
from cg.utils import Process
from cg.utils.dict import get_list_from_dictionary

LOG = logging.getLogger(__name__)


class LoqusdbAPI:
    """API for Loqusdb."""

    def __init__(self, binary_path: str, config_path: str):
        self.binary_path = binary_path
        self.config_path = config_path
        self.process = Process(binary=self.binary_path, config=self.config_path)

    def load(
        self,
        case_id: str,
        snv_vcf_path: Path,
        sv_vcf_path: Path | None = None,
        profile_vcf_path: Path | None = None,
        family_ped_path: Path | None = None,
        window_size: int | None = None,
        gq_threshold: int | None = None,
        qual_gq: bool | None = False,
        hard_threshold: float | None = None,
        soft_threshold: float | None = None,
        snv_gq_only: bool | None = False,
        loqusdb_options: list[str] | None = None,
    ) -> dict[str, int]:
        """Add observations to Loqusdb from VCF files."""
        load_params = {
            "--case-id": case_id,
            "--variant-file": snv_vcf_path.as_posix(),
            "--sv-variants": sv_vcf_path.as_posix() if sv_vcf_path else None,
            "--check-profile": profile_vcf_path.as_posix() if profile_vcf_path else None,
            "--family-file": family_ped_path.as_posix() if family_ped_path else None,
            "--max-window": str(window_size) if window_size else None,
            "--gq-threshold": str(gq_threshold) if gq_threshold else None,
            "--hard-threshold": str(hard_threshold) if hard_threshold else None,
            "--soft-threshold": str(soft_threshold) if soft_threshold else None,
        }
        load_call_params: list[str] = (
            (loqusdb_options or []) + ["load"] + get_list_from_dictionary(load_params)
        )
        load_call_params.append("--qual-gq") if qual_gq else None
        load_call_params.append("--snv-gq-only") if snv_gq_only else None
        self.process.run_command(parameters=load_call_params)
        return self.get_nr_of_variants_in_file()

    def get_case(self, case_id: str) -> dict | None:
        """Return a case found in Loqusdb."""
        cases_parameters = ["cases", "-c", case_id, "--to-json"]
        self.process.run_command(parameters=cases_parameters)
        if not self.process.stdout:  # Case not in loqusdb, stdout of loqusdb command will be empty.
            LOG.info(f"Case {case_id} not found in {repr(self)}")
            return None

        return ReadStream.get_content_from_stream(
            file_format=FileFormat.JSON, stream=self.process.stdout
        )[0]

    def get_duplicate(self, profile_vcf_path: Path, profile_threshold: float) -> dict | None:
        """Find matching profiles in Loqusdb."""
        duplicates_params = {
            "--check-vcf": profile_vcf_path.as_posix(),
            "--profile-threshold": str(profile_threshold),
        }
        duplicate_call_params: list = ["profile"] + get_list_from_dictionary(duplicates_params)

        try:
            self.process.run_command(parameters=duplicate_call_params)
        except CalledProcessError as exception:
            LOG.error(f"Could not execute the profile command for: {profile_vcf_path.as_posix()}")
            raise exception
        if not self.process.stdout:
            LOG.info(f"No duplicates found for profile: {profile_vcf_path.as_posix()}")
            return None

        return ReadStream.get_content_from_stream(
            file_format=FileFormat.JSON, stream=self.process.stdout
        )

    def delete_case(self, case_id: str) -> None:
        """Remove a case from Loqusdb."""
        delete_call_parameters = ["delete", "-c", case_id]
        self.process.run_command(parameters=delete_call_parameters)
        for line in self.process.stderr_lines():
            if f"INFO Removing case {case_id}" in line:
                LOG.info(f"Removing case {case_id} from {repr(self)}")
                return
            if f"WARNING Case {case_id} does not exist" in line:
                LOG.error(f"Case {case_id} not found in {repr(self)}")
                raise CaseNotFoundError

        LOG.error(f"Could not delete case {case_id} from {repr(self)}")
        raise LoqusdbDeleteCaseError

    def get_nr_of_variants_in_file(self) -> dict[str, int]:
        """Return the number of variants in the uploaded to Loqusdb file."""
        nr_of_variants: int = 0
        for line in self.process.stderr_lines():
            line_content: str = line.split("INFO")[-1].strip()
            if "inserted" in line_content:
                nr_of_variants = int(line_content.split(":")[-1].strip())
        return {"variants": nr_of_variants}

    def __repr__(self):
        return f"LoqusdbAPI(binary_path={Path(self.binary_path).name}, config_path={Path(self.config_path).name})"
