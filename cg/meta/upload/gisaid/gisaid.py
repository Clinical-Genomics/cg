"""GISAID API."""

import logging
import re
import tempfile
from pathlib import Path

import pandas as pd
from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.constants.constants import SARS_COV_REGEX, FileFormat
from cg.exc import HousekeeperFileMissingError
from cg.io.controller import ReadFile, WriteFile
from cg.io.csv import write_csv_from_dict
from cg.models.cg_config import CGConfig
from cg.models.gisaid.reports import GisaidComplementaryReport
from cg.store.models import Sample
from cg.store.store import Store
from cg.utils import Process
from cg.utils.dict import remove_duplicate_dicts

from .constants import HEADERS
from .models import GisaidAccession, GisaidSample

LOG = logging.getLogger(__name__)

UPLOADED_REGEX_MATCH = r"\[\"([A-Za-z0-9_]+)\"\]\}$"


class GisaidAPI:
    """Interface with Gisaid CLI upload."""

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
        self.email_base_settings = config.email_base_settings
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
        complementary_reports = []
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
        """Return all unique samples in reports."""
        return {report.sample_number for report in reports}

    def get_complementary_report_samples(self, sample_numbers: set[str]) -> list[Sample]:
        """Return all unique samples in reports."""
        return [
            self.status_db.get_sample_by_name(name=sample_number)
            for sample_number in sample_numbers
        ]

    def get_complementary_file_from_hk(self, case_id: str) -> File:
        """Return complementary file."""
        complementary_file: File | None = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags=["komplettering"]
        )
        if not complementary_file:
            msg = f"completion file missing for bundle: {case_id}"
            raise HousekeeperFileMissingError(message=msg)
        return complementary_file

    def get_completion_dataframe(self, completion_file: File) -> pd.DataFrame:
        """Read completion file in to dataframe, drop duplicates, and return the dataframe"""
        completion_df = pd.read_csv(completion_file.full_path, index_col=None, header=0)
        completion_df.drop_duplicates(inplace=True)
        completion_df = completion_df[completion_df["provnummer"].str.contains(SARS_COV_REGEX)]
        return completion_df

    def get_gisaid_sample_list(self, case_id: str) -> list[Sample]:
        """Get list of Sample objects eligeble for upload.
        The criteria is that the sample reached 20x coverage for >95% bases.
        The sample will be included in completion file."""

        completion_file = self.get_complementary_file_from_hk(case_id=case_id)
        completion_df = self.get_completion_dataframe(completion_file=completion_file)
        sample_names = list(completion_df["provnummer"].unique())
        return [self.status_db.get_sample_by_name(name=sample_name) for sample_name in sample_names]

    def get_gisaid_fasta_path(self, case_id: str) -> Path:
        """Get path to gisaid fasta"""
        return Path(self.mutant_root_dir, case_id, "results", f"{case_id}.fasta")

    def get_gisaid_csv_path(self, case_id: str) -> Path:
        """Get path to gisaid csv"""
        return Path(self.mutant_root_dir, case_id, "results", f"{case_id}.csv")

    def get_gisaid_samples_csv(self, case_id: str, samples: list[Sample]) -> list[GisaidSample]:
        """Return Gisaid samples."""
        gisaid_samples = []
        for sample in samples:
            sample_id: str = sample.internal_id
            LOG.info(f"Creating GisaidSample for {sample_id}")
            gisaid_sample = GisaidSample(
                case_id=case_id,
                cg_lims_id=sample_id,
                covv_subm_sample_id=sample.name,
                submitter=self.gisaid_submitter,
                fn=f"{case_id}.fasta",
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

    def get_gisaid_samples(self, case_id: str) -> list[GisaidSample]:
        """Get list of Gisaid sample objects."""

        samples: list[Sample] = self.get_gisaid_sample_list(case_id=case_id)
        gisaid_samples = []
        for sample in samples:
            sample_id: str = sample.internal_id
            LOG.info(f"Creating GisaidSample for {sample_id}")
            gisaid_sample = GisaidSample(
                case_id=case_id,
                cg_lims_id=sample_id,
                covv_subm_sample_id=sample.name,
                submitter=self.gisaid_submitter,
                fn=f"{case_id}.fasta",
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

    def create_gisaid_fasta(self, gisaid_samples: list[GisaidSample], case_id: str) -> None:
        """Writing a new fasta with headers adjusted for gisaid upload_results_to_gisaid"""

        gisaid_fasta_file = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags=["gisaid-fasta", case_id]
        )
        if gisaid_fasta_file:
            gisaid_fasta_path = gisaid_fasta_file.full_path
        else:
            gisaid_fasta_path: Path = self.get_gisaid_fasta_path(case_id=case_id)

        fasta_lines: list[str] = []

        for sample in gisaid_samples:
            fasta_file: File = self.housekeeper_api.get_file_from_latest_version(
                bundle_name=case_id, tags=[sample.cg_lims_id, "consensus-sample"]
            )
            if not fasta_file:
                raise HousekeeperFileMissingError(
                    message=f"No fasta file found for sample {sample.cg_lims_id}"
                )
            with open(str(fasta_file.full_path)) as handle:
                for line in handle.readlines():
                    if line[0] == ">":
                        fasta_lines.append(f">{sample.covv_virus_name}\n")
                    else:
                        fasta_lines.append(line)

        with open(gisaid_fasta_path, "w") as write_file_obj:
            write_file_obj.writelines(fasta_lines)

        if gisaid_fasta_file:
            return

        self.housekeeper_api.add_and_include_file_to_latest_version(
            bundle_name=case_id, file=gisaid_fasta_path, tags=["gisaid-fasta", case_id]
        )

    def create_gisaid_csv_hs(self, gisaid_samples: list[GisaidSample], case_id: str) -> None:
        """Create CSV file for GISAID samples."""
        gisaid_csv_file: File | None = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags=["gisaid-csv", case_id]
        )
        if gisaid_csv_file:
            LOG.info(f"GISAID CSV for case {case_id} exists, will be replaced")
            gisaid_csv_path = gisaid_csv_file.full_path
        else:
            gisaid_csv_path: Path = self.get_gisaid_csv_path(case_id=case_id)
        all_samples: list[dict] = [sample.model_dump() for sample in gisaid_samples]
        write_csv_from_dict(content=all_samples, fieldnames=HEADERS, file_path=gisaid_csv_path)

        if gisaid_csv_file:
            return

        self.housekeeper_api.add_and_include_file_to_latest_version(
            bundle_name=case_id, file=gisaid_csv_path, tags=["gisaid-csv", case_id]
        )

    def create_gisaid_csv(self, gisaid_samples: list[GisaidSample], case_id: str) -> None:
        """Create csv file for gisaid upload"""
        samples_df = pd.DataFrame(
            data=[gisaid_sample.model_dump() for gisaid_sample in gisaid_samples],
            columns=HEADERS,
        )

        gisaid_csv_file = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags=["gisaid-csv", case_id]
        )
        if gisaid_csv_file:
            LOG.info(f"GISAID CSV for case {case_id} exists, will be replaced")
            gisaid_csv_path = gisaid_csv_file.full_path
        else:
            gisaid_csv_path = self.get_gisaid_csv_path(case_id=case_id)
        samples_df.to_csv(gisaid_csv_path, sep=",", index=False)

        if gisaid_csv_file:
            return

        self.housekeeper_api.add_and_include_file_to_latest_version(
            bundle_name=case_id, file=gisaid_csv_path, tags=["gisaid-csv", case_id]
        )

    def create_gisaid_log_file(self, case_id: str) -> None:
        """Path for gisaid bundle log"""
        if _ := self.housekeeper_api.get_files(
            bundle=case_id, tags=["gisaid-log", case_id]
        ).first():
            LOG.info("GISAID log exists in case bundle in Housekeeper")
            return

        log_file_path = Path(self.gisaid_log_dir, case_id).with_suffix(".log")
        if not log_file_path.parent.exists():
            raise ValueError(f"GISAID log dir: {self.gisaid_log_dir} does not exist")
        if not log_file_path.exists():
            log_file_path.touch()
        self.housekeeper_api.add_and_include_file_to_latest_version(
            bundle_name=case_id, file=log_file_path, tags=["gisaid-log", case_id]
        )

    def create_gisaid_files_in_housekeeper(self, case_id: str) -> None:
        """Create all gisaid files in Housekeeper, if needed."""
        gisaid_samples = self.get_gisaid_samples(case_id=case_id)
        self.create_gisaid_csv(gisaid_samples=gisaid_samples, case_id=case_id)
        self.create_gisaid_fasta(gisaid_samples=gisaid_samples, case_id=case_id)
        self.create_gisaid_log_file(case_id=case_id)

    def create_gisaid_files_in_housekeeper_csv(self, case_id: str) -> None:
        """Create all GISAID files in Housekeeper."""
        complementary_report_file: Path = self.get_complementary_file_from_hk(case_id)
        complementary_report_content_raw: list[dict] = self.get_complementary_report_content(
            complementary_report_file
        )
        complementary_report_content_raw_unique: list[dict] = remove_duplicate_dicts(
            complementary_report_content_raw
        )
        complementary_report: list[GisaidComplementaryReport] = (
            self.validate_gisaid_complementary_reports(complementary_report_content_raw_unique)
        )
        complementary_report: list[GisaidComplementaryReport] = (
            self.get_sars_cov_complementary_reports(complementary_report)
        )
        sample_numbers: set[str] = self.get_complementary_report_sample_number(complementary_report)
        samples: list[Sample] = self.get_complementary_report_samples(sample_numbers)

        gisaid_samples: list[GisaidSample] = self.get_gisaid_samples_csv(
            case_id=case_id, samples=samples
        )
        self.create_gisaid_csv_hs(case_id=case_id, gisaid_samples=gisaid_samples)
        self.create_gisaid_fasta(gisaid_samples=gisaid_samples, case_id=case_id)
        self.create_gisaid_log_file(case_id=case_id)

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
        """Load batch data to GISAID using the gisiad cli."""

        temp_log_file = tempfile.NamedTemporaryFile(
            dir=self.gisaid_log_dir, mode="w+", delete=False
        )
        gisaid_csv_path = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags=["gisaid-csv", case_id]
        ).full_path

        gisaid_fasta_path = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags=["gisaid-fasta", case_id]
        ).full_path

        gisaid_log_path = (
            self.housekeeper_api.get_files(bundle=case_id, tags=["gisaid-log", case_id])
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
            gisaid_csv_path,
            "--fasta",
            gisaid_fasta_path,
        ]
        self.process.run_command(parameters=load_call)
        self.append_log(temp_log=Path(temp_log_file.name), gisaid_log=Path(gisaid_log_path))
        temp_log_file.close()
        if self.process.stderr:
            LOG.info(f"gisaid stderr:\n{self.process.stderr}")
        if self.process.stdout:
            LOG.info(f"gisaid stdout:\n{self.process.stdout}")

    def append_log(self, temp_log: Path, gisaid_log: Path) -> None:
        """Appends temp log to gisaid log and delete temp file"""
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

    def get_accession_numbers(self, case_id: str) -> dict[str, str]:
        """Parse accession numbers and sample ids from log file"""

        LOG.info("Parsing accession numbers from log file")
        accession_numbers = {}
        log_file = Path(
            self.housekeeper_api.get_files(bundle=case_id, tags=["gisaid-log", case_id])
            .first()
            .full_path
        )
        if log_file.stat().st_size != 0:
            log_data = ReadFile.get_content_from_file(
                file_format=FileFormat.JSON, file_path=log_file.absolute()
            )
            for log in log_data:
                if log.get("code") == "epi_isl_id":
                    log_message = log.get("msg")
                elif log.get("code") == "validation_error" and "existing_ids" in log.get("msg"):
                    log_message = (
                        f'{log.get("msg").split(";")[0]}; '
                        f'{re.findall(UPLOADED_REGEX_MATCH, log.get("msg"))[0]}'
                    )
                else:
                    continue
                accession_obj = GisaidAccession(log_message=log_message)
                accession_numbers[accession_obj.sample_id] = accession_obj.accession_nr
        return accession_numbers

    def update_completion_file(self, case_id: str) -> None:
        """Update completion file with accession numbers"""
        completion_file = self.get_complementary_file_from_hk(case_id=case_id)
        accession_dict = self.get_accession_numbers(case_id=case_id)
        completion_df = self.get_completion_dataframe(completion_file=completion_file)
        completion_df["GISAID_accession"] = completion_df["provnummer"].apply(
            lambda x: accession_dict[x]
        )
        completion_df.to_csv(
            completion_file.full_path,
            sep=",",
            index=False,
        )

    def upload(self, case_id: str) -> None:
        """Uploading results to gisaid and saving the accession numbers in completion file"""

        completion_file = self.get_complementary_file_from_hk(case_id=case_id)
        completion_df = self.get_completion_dataframe(completion_file=completion_file)
        if len(completion_df["GISAID_accession"].dropna()) == len(completion_df["provnummer"]):
            LOG.info("All samples already uploaded")
            return

        self.create_gisaid_files_in_housekeeper(case_id=case_id)
        self.upload_results_to_gisaid(case_id=case_id)
        self.update_completion_file(case_id=case_id)
