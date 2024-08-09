"""GISAID API."""

import logging
import re
import tempfile
from pathlib import Path

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.constants import FileExtensions
from cg.constants.constants import SARS_COV_REGEX, FileFormat
from cg.constants.housekeeper_tags import FohmTag, GisaidTag
from cg.exc import HousekeeperFileMissingError
from cg.io.controller import ReadFile, WriteFile
from cg.io.csv import write_csv_from_dict
from cg.meta.upload.gisaid.constants import HEADERS
from cg.meta.upload.gisaid.models import GisaidAccession, GisaidSample
from cg.models.cg_config import CGConfig, EmailBaseSettings
from cg.models.gisaid.reports import GisaidComplementaryReport
from cg.store.models import Sample
from cg.store.store import Store
from cg.utils import Process
from cg.utils.dict import remove_duplicate_dicts

LOG = logging.getLogger(__name__)

UPLOADED_REGEX_MATCH = r"\[\"([A-Za-z0-9_]+)\"\]\}$"


class GisaidAPI:
    """Interface with GISAID CLI."""

    def __init__(self, config: CGConfig):
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.lims_api: LimsAPI = config.lims_api
        self.status_db: Store = config.status_db
        self.gisaid_submitter: str = config.gisaid.submitter
        self.upload_password: str = config.gisaid.upload_password
        self.upload_cid: str = config.gisaid.upload_cid
        self.gisaid_binary: str = config.gisaid.binary_path
        self.gisaid_log_dir: str = config.gisaid.log_dir
        self.log_watch: str = config.gisaid.logwatch_email
        self.email_base_settings: EmailBaseSettings = config.email_base_settings
        self.mutant_root_dir = Path(config.mutant.root)
        self.process = Process(binary=self.gisaid_binary)

    @staticmethod
    def get_complementary_report_content(complementary_file: Path) -> list[dict]:
        """Return complementary report content from file."""
        return ReadFile.get_content_from_file(
            file_format=FileFormat.CSV, file_path=complementary_file, read_to_dict=True
        )

    @staticmethod
    def validate_gisaid_complementary_reports(
        reports: list[dict],
    ) -> list[GisaidComplementaryReport]:
        """Validate GISAID complementary reports.
        Raises:
            ValidateError."""
        complementary_reports: list[GisaidComplementaryReport] = []
        for report in reports:
            complementary_report = GisaidComplementaryReport.model_validate(report)
            complementary_reports.append(complementary_report)
        return complementary_reports

    @staticmethod
    def get_sars_cov_complementary_reports(
        reports: list[GisaidComplementaryReport],
    ) -> list[GisaidComplementaryReport]:
        """Return all "Sars-cov2" reports."""
        return [report for report in reports if re.search(SARS_COV_REGEX, report.sample_number)]

    @staticmethod
    def get_complementary_report_sample_number(
        reports: list[GisaidComplementaryReport],
    ) -> set[str]:
        """Return all unique sample numbers in reports."""
        return {report.sample_number for report in reports}

    @staticmethod
    def add_gisaid_accession_to_complementary_reports(
        gisaid_accession: dict[str, str], reports: list[GisaidComplementaryReport]
    ) -> None:
        """Add GISAID accession to complementary reports."""
        for report in reports:
            report.gisaid_accession = gisaid_accession[report.sample_number]

    def get_complementary_report_samples(self, sample_numbers: set[str]) -> list[Sample]:
        """Return all unique samples in reports."""
        return [
            self.status_db.get_sample_by_name(name=sample_number)
            for sample_number in sample_numbers
        ]

    def get_complementary_file_from_hk(self, case_id: str) -> File:
        """Return complementary file from Housekeeper."""
        complementary_file: File | None = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags={FohmTag.COMPLEMENTARY}
        )
        if not complementary_file:
            msg = f"Complementary file missing for bundle: {case_id}"
            raise HousekeeperFileMissingError(message=msg)
        return complementary_file

    def get_gisaid_fasta_file_path(self, case_id: str) -> Path:
        """Return the path to GISAID FASTA file."""
        return Path(self.mutant_root_dir, case_id, "results", f"{case_id}{FileExtensions.FASTA}")

    def get_gisaid_csv_path(self, case_id: str) -> Path:
        """Return the path to GISAID CSV file."""
        return Path(self.mutant_root_dir, case_id, "results", f"{case_id}{FileExtensions.CSV}")

    def get_gisaid_samples(self, case_id: str, samples: list[Sample]) -> list[GisaidSample]:
        """Return GISAID samples."""
        gisaid_samples: list[GisaidSample] = []
        for sample in samples:
            sample_id: str = sample.internal_id
            LOG.info(f"Creating GisaidSample for {sample_id}")
            gisaid_sample = GisaidSample(
                case_id=case_id,
                cg_lims_id=sample_id,
                covv_subm_sample_id=sample.name,
                submitter=self.gisaid_submitter,
                fn=f"{case_id}{FileExtensions.FASTA}",
                covv_collection_date=str(
                    self.lims_api.get_sample_attribute(lims_id=sample_id, key="collection_date")
                ),
                region=self.lims_api.get_sample_attribute(lims_id=sample_id, key="region"),
                region_code=self.lims_api.get_sample_attribute(
                    lims_id=sample_id, key="region_code"
                ),
                covv_orig_lab=self.lims_api.get_sample_attribute(
                    lims_id=sample_id, key="original_lab"
                ),
                covv_orig_lab_addr=self.lims_api.get_sample_attribute(
                    lims_id=sample_id, key="original_lab_address"
                ),
            )
            gisaid_samples.append(gisaid_sample)
        return gisaid_samples

    def create_and_include_gisaid_fasta_to_hk(
        self, gisaid_samples: list[GisaidSample], case_id: str
    ) -> None:
        """Create and include a FASTA with headers adjusted for GISAID upload results to GISAID."""

        gisaid_fasta: File | None = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags={GisaidTag.FASTA, case_id}
        )
        if gisaid_fasta:
            gisaid_fasta_file = Path(gisaid_fasta.full_path)
        else:
            gisaid_fasta_file: Path = self.get_gisaid_fasta_file_path(case_id=case_id)

        fasta_lines: list[str] = []

        for sample in gisaid_samples:
            fasta_file: File | None = self.housekeeper_api.get_file_from_latest_version(
                bundle_name=case_id, tags={sample.cg_lims_id, GisaidTag.CONSENSUS_SAMPLE}
            )
            if not fasta_file:
                raise HousekeeperFileMissingError(
                    message=f"No FASTA file found for sample {sample.cg_lims_id}"
                )
            with open(fasta_file.full_path) as read_handle:
                for line in read_handle:
                    if line[0] == ">":
                        fasta_lines.append(f">{sample.covv_virus_name}\n")
                    else:
                        fasta_lines.append(line)

        with open(gisaid_fasta_file, "w") as write_handle:
            write_handle.writelines(fasta_lines)

        if gisaid_fasta:
            return

        self.housekeeper_api.add_and_include_file_to_latest_version(
            bundle_name=case_id, file=gisaid_fasta_file, tags=[GisaidTag.FASTA, case_id]
        )

    def create_and_include_gisaid_samples_to_hk(
        self, gisaid_samples: list[GisaidSample], case_id: str
    ) -> None:
        """Create and include CSV file for GISAID samples to Housekeeper."""
        gisaid_samples_csv: File | None = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags={GisaidTag.CSV, case_id}
        )
        if gisaid_samples_csv:
            LOG.info(f"GISAID samples CSV for case {case_id} exists, and will be replaced")
            gisaid_csv_file = Path(gisaid_samples_csv.full_path)
        else:
            gisaid_csv_file: Path = self.get_gisaid_csv_path(case_id=case_id)
        samples: list[dict] = [sample.model_dump() for sample in gisaid_samples]
        write_csv_from_dict(content=samples, fieldnames=HEADERS, file_path=gisaid_csv_file)
        if gisaid_samples_csv:
            return
        self.housekeeper_api.add_and_include_file_to_latest_version(
            bundle_name=case_id, file=gisaid_csv_file, tags=[GisaidTag.CSV, case_id]
        )

    def create_and_include_gisaid_log_file_to_hk(self, case_id: str) -> None:
        """Create and include GISAID log file to a Housekeeper."""
        if _ := self.housekeeper_api.get_files(
            bundle=case_id, tags=[GisaidTag.LOG, case_id]
        ).first():
            LOG.info(f"GISAID log exists in case: {case_id} bundle in Housekeeper")
            return

        log_file = Path(self.gisaid_log_dir, case_id).with_suffix(FileExtensions.LOG)
        if not log_file.parent.exists():
            raise ValueError(f"GISAID log dir: {self.gisaid_log_dir} does not exist")
        if not log_file.exists():
            log_file.touch()
        self.housekeeper_api.add_and_include_file_to_latest_version(
            bundle_name=case_id, file=log_file, tags=[GisaidTag.LOG, case_id]
        )

    def parse_and_get_sars_cov_complementary_reports(
        self, complementary_report_file: Path
    ) -> list[GisaidComplementaryReport]:
        complementary_report_content_raw: list[dict] = self.get_complementary_report_content(
            complementary_report_file
        )
        complementary_report_content_raw_unique: list[dict] = remove_duplicate_dicts(
            complementary_report_content_raw
        )
        complementary_report_sars_cov: list[GisaidComplementaryReport] = (
            self.validate_gisaid_complementary_reports(complementary_report_content_raw_unique)
        )
        return self.get_sars_cov_complementary_reports(complementary_report_sars_cov)

    def create_and_include_gisaid_files_in_hk(self, case_id: str) -> None:
        """Create and include all GISAID files in Housekeeper."""
        complementary_report_file: Path = self.get_complementary_file_from_hk(case_id)
        sars_cov_complementary_reports: list[GisaidComplementaryReport] = (
            self.parse_and_get_sars_cov_complementary_reports(complementary_report_file)
        )
        sample_numbers: set[str] = self.get_complementary_report_sample_number(
            sars_cov_complementary_reports
        )
        samples: list[Sample] = self.get_complementary_report_samples(sample_numbers)

        gisaid_samples: list[GisaidSample] = self.get_gisaid_samples(
            case_id=case_id, samples=samples
        )
        self.create_and_include_gisaid_samples_to_hk(gisaid_samples=gisaid_samples, case_id=case_id)
        self.create_and_include_gisaid_fasta_to_hk(gisaid_samples=gisaid_samples, case_id=case_id)
        self.create_and_include_gisaid_log_file_to_hk(case_id)

    def authenticate_gisaid(self):
        load_call: list = [
            "CoV",
            "authenticate",
            "--cid",
            self.upload_cid,
            "--user",
            self.gisaid_submitter,
            "--pass",
            self.upload_password,
        ]
        self.process.run_command(parameters=load_call)

    def upload_results_to_gisaid(self, case_id: str) -> None:
        """Load batch data to GISAID using the GISAID CLI."""

        temp_log_file = tempfile.NamedTemporaryFile(
            dir=self.gisaid_log_dir, mode="w+", delete=False
        )
        gisaid_csv_file: str = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags={GisaidTag.CSV, case_id}
        ).full_path

        gisaid_fasta_file: str = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags={GisaidTag.FASTA, case_id}
        ).full_path

        gisaid_log_file: str = (
            self.housekeeper_api.get_files(bundle=case_id, tags=[GisaidTag.LOG, case_id])
            .first()
            .full_path
        )

        self.authenticate_gisaid()
        load_call: list = [
            "--logfile",
            temp_log_file.name,
            "CoV",
            "upload",
            "--csv",
            gisaid_csv_file,
            "--fasta",
            gisaid_fasta_file,
        ]
        self.process.run_command(parameters=load_call)
        self.append_to_gisaid_log(
            temp_log=Path(temp_log_file.name), gisaid_log=Path(gisaid_log_file)
        )
        temp_log_file.close()
        if self.process.stderr:
            LOG.info(f"gisaid stderr:\n{self.process.stderr}")
        if self.process.stdout:
            LOG.info(f"gisaid stdout:\n{self.process.stdout}")

    def append_to_gisaid_log(self, temp_log: Path, gisaid_log: Path) -> None:
        """Appends temp log to GISAID log and delete temp file."""
        new_log_data = ReadFile.get_content_from_file(
            file_format=FileFormat.JSON, file_path=temp_log.absolute()
        )
        if gisaid_log.stat().st_size != 0:
            old_log_data = ReadFile.get_content_from_file(
                file_format=FileFormat.JSON, file_path=gisaid_log.absolute()
            )
            new_log_data.extend(old_log_data)

        WriteFile.write_file_from_content(
            content=new_log_data, file_format=FileFormat.JSON, file_path=gisaid_log.absolute()
        )
        temp_log.unlink()

    def get_gisaid_accession_numbers(self, case_id: str) -> dict[str, str]:
        """Parse and return GISAID accession numbers and sample ids from log file."""
        log_file = Path(
            self.housekeeper_api.get_files(bundle=case_id, tags=["gisaid-log", case_id])
            .first()
            .full_path
        )
        LOG.info(f"Parsing accession numbers from log file: {log_file}")
        accession_numbers = {}

        if log_file.stat().st_size != 0:
            log_contents: list[dict] = ReadFile.get_content_from_file(
                file_format=FileFormat.JSON, file_path=log_file.absolute()
            )
            for log in log_contents:
                if log.get("code") == "epi_isl_id":
                    log_message = log.get("msg")
                elif log.get("code") == "validation_error" and "existing_ids" in log.get("msg"):
                    log_message = (
                        f'{log.get("msg").split(";")[0]}; '
                        f'{re.findall(UPLOADED_REGEX_MATCH, log.get("msg"))[0]}'
                    )
                else:
                    continue
                gisaid_accession = GisaidAccession(log_message=log_message)
                accession_numbers[gisaid_accession.sample_id] = gisaid_accession.accession_nr
        return accession_numbers

    def update_complementary_file_with_gisaid_accessions(self, case_id: str) -> None:
        """Update complementary file with GISAID accession numbers."""
        complementary_report: File | None = self.get_complementary_file_from_hk(case_id=case_id)
        accession: dict = self.get_gisaid_accession_numbers(case_id=case_id)
        sars_cov_complementary_reports: list[GisaidComplementaryReport] = (
            self.parse_and_get_sars_cov_complementary_reports(Path(complementary_report.full_path))
        )
        self.add_gisaid_accession_to_complementary_reports(
            gisaid_accession=accession, reports=sars_cov_complementary_reports
        )
        reports: list[dict] = [report.model_dump() for report in sars_cov_complementary_reports]
        write_csv_from_dict(
            content=reports, fieldnames=HEADERS, file_path=Path(complementary_report.full_path)
        )

    def upload_to_gisaid(self, case_id: str) -> None:
        """Uploading results to GISAID and saving the accession numbers in complementary file."""
        gisaid_accession_count: int = 0
        sample_number_count: int = 0
        complementary_report_file: File | None = self.get_complementary_file_from_hk(case_id)
        sars_cov_complementary_reports: list[GisaidComplementaryReport] = (
            self.parse_and_get_sars_cov_complementary_reports(complementary_report_file)
        )
        for report in sars_cov_complementary_reports:
            if report.gisaid_accession:
                gisaid_accession_count += 1
            if report.sample_number:
                sample_number_count += 1
        if gisaid_accession_count == sample_number_count:
            LOG.info("All samples already uploaded")
            return

        self.create_and_include_gisaid_files_in_hk(case_id=case_id)
        self.upload_results_to_gisaid(case_id=case_id)
        self.update_complementary_file_with_gisaid_accessions(case_id=case_id)
