"""Interactions with the gisaid cli upload_results_to_gisaid"""

import csv
import logging
import re
import tempfile
from collections.abc import ValuesView
from pathlib import Path

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.constants.constants import SARS_COV_REGEX, FileFormat
from cg.constants.housekeeper_tags import FohmTag
from cg.exc import CgError, HousekeeperFileMissingError
from cg.io.controller import ReadFile, WriteFile
from cg.meta.upload.gisaid.constants import HEADERS
from cg.meta.upload.gisaid.models import GisaidAccession, GisaidSample
from cg.models.cg_config import CGConfig
from cg.store.models import Sample
from cg.store.store import Store
from cg.utils import Process

LOG = logging.getLogger(__name__)

UPLOADED_REGEX_MATCH = r"\[\"([A-Za-z0-9_]+)\"\]\}$"


class GisaidAPI:
    """Interface with Gisaid cli uppload"""

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

    def get_completion_file_from_hk(self, case_id: str) -> File:
        """Return completion file.
        Raises:
            HousekeeperFileMissingError."""

        completion_file: File | None = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags={FohmTag.COMPLEMENTARY}
        )
        if not completion_file:
            msg = f"Completion file missing for bundle {case_id}"
            raise HousekeeperFileMissingError(message=msg)
        return completion_file

    def get_completion_dict(self, completion_file: File):
        """Read completion file in to dictionary similar to a pandas dataframe and drop duplicates"""
        with open(Path(completion_file.full_path), "r") as file:
            csv_reader: csv.DictReader = csv.DictReader(file)
            if not csv_reader.fieldnames:
                raise CgError(f"{completion_file.full_path} is malformed.")

            deduplicated_csv: ValuesView = {tuple(row.items()): row for row in csv_reader}.values()
            completion_dict: dict = {field: {} for field in csv_reader.fieldnames}

            for i, row in enumerate(deduplicated_csv):
                if not re.match(SARS_COV_REGEX, row["provnummer"]):
                    continue
                for key, value in row.items():
                    completion_dict[key][i] = value

        return completion_dict

    def get_gisaid_sample_list(self, case_id: str) -> list[Sample]:
        """Get list of Sample objects eligeble for upload.
        The criteria is that the sample reached 20x coverage for >95% bases.
        The sample will be included in completion file."""

        completion_file = self.get_completion_file_from_hk(case_id=case_id)
        completion_dict = self.get_completion_dict(completion_file=completion_file)
        # deduplicate by provnummer and preserve order to match legacy pandas unique()
        sample_names = list(dict.fromkeys(completion_dict["provnummer"].values()))
        return [self.status_db.get_sample_by_name(name=sample_name) for sample_name in sample_names]

    def get_gisaid_fasta_path(self, case_id: str) -> Path:
        """Get path to gisaid fasta"""
        return Path(self.mutant_root_dir, case_id, "results", f"{case_id}.fasta")

    def get_gisaid_csv_path(self, case_id: str) -> Path:
        """Get path to gisaid csv"""
        return Path(self.mutant_root_dir, case_id, "results", f"{case_id}.csv")

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

    def create_gisaid_csv(self, gisaid_samples: list[GisaidSample], case_id: str) -> None:
        """Create csv file for gisaid upload"""
        sample_dicts: list[dict] = [
            sample.model_dump(include=set(HEADERS)) for sample in gisaid_samples
        ]

        gisaid_csv_file = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags=["gisaid-csv", case_id]
        )
        if gisaid_csv_file:
            LOG.info(f"GISAID CSV for case {case_id} exists, will be replaced")
            gisaid_csv_path = gisaid_csv_file.full_path
        else:
            gisaid_csv_path = self.get_gisaid_csv_path(case_id=case_id)

        with open(Path(gisaid_csv_path), "w", newline="") as csv_file:
            writer: csv.DictWriter = csv.DictWriter(csv_file, fieldnames=HEADERS)
            writer.writeheader()
            writer.writerows(sample_dicts)

        if gisaid_csv_file:
            return

        self.housekeeper_api.add_and_include_file_to_latest_version(
            bundle_name=case_id, file=gisaid_csv_path, tags=["gisaid-csv", case_id]
        )

    def create_gisaid_log_file(self, case_id: str) -> None:
        """Path for gisaid bundle log"""
        gisaid_log_file = self.housekeeper_api.get_files(
            bundle=case_id, tags=["gisaid-log", case_id]
        ).first()
        if gisaid_log_file:
            LOG.info("GISAID log exists in case bundle in Housekeeper")
            return

        log_file_path = Path(self.gisaid_log_dir, case_id).with_suffix(".log")
        if not log_file_path.parent.exists():
            raise ValueError(f"Gisaid log dir: {self.gisaid_log_dir} doesnt exist")
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
        completion_file = self.get_completion_file_from_hk(case_id=case_id)
        accession_dict = self.get_accession_numbers(case_id=case_id)
        completion_dict = self.get_completion_dict(completion_file=completion_file)

        for index, completion_provnummer in completion_dict["provnummer"].items():
            new_value = accession_dict[completion_provnummer]
            completion_dict["GISAID_accession"][index] = new_value

        fieldnames = list(completion_dict.keys())
        indices = list(next(iter(completion_dict.values())).keys())
        rows = [{col: completion_dict[col][i] for col in fieldnames} for i in indices]

        with open(completion_file.full_path, "w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def upload(self, case_id: str) -> None:
        """Uploading results to gisaid and saving the accession numbers in completion file"""

        completion_file = self.get_completion_file_from_hk(case_id=case_id)
        completion_dict = self.get_completion_dict(completion_file=completion_file)
        if self._all_samples_uploaded_dict(completion_dict):
            LOG.info("All samples already uploaded")
            return

        self.create_gisaid_files_in_housekeeper(case_id=case_id)
        self.upload_results_to_gisaid(case_id=case_id)
        self.update_completion_file(case_id=case_id)

    def _all_samples_uploaded_dict(self, completion_dict: dict) -> bool:
        if not completion_dict["provnummer"]:
            return True

        accession_values = [
            value for value in completion_dict["GISAID_accession"].values() if value
        ]
        return len(accession_values) == len(completion_dict["provnummer"])
