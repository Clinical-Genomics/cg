"""Interactions with the gisaid cli upload_results_to_gisaid"""
import json
import logging
from datetime import date
from pathlib import Path
from typing import List, Dict, Optional

from housekeeper.store.models import File
import tempfile

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.models.cg_config import CGConfig
from cg.store import models, Store
from cg.utils import Process
from .constants import HEADERS
from .models import GisaidSample, UploadFiles, GisaidAccession
import csv

from cg.exc import (
    FastaSequenceMissingError,
    AccessionNumerMissingError,
    GisaidUploadFailedError,
    InvalidFastaError,
    HousekeeperFileMissingError,
)

LOG = logging.getLogger(__name__)


class GisaidAPI:
    """Interface with Gisaid cli uppload"""

    def __init__(self, config: CGConfig):
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.lims_api: LimsAPI = config.lims_api
        self.status_db: Store = config.status_db
        self.gisaid_submitter: str = config.gisaid.submitter
        self.gisaid_binary: str = config.gisaid.binary_path
        self.gisaid_log_dir: str = config.gisaid.log_dir
        self.log_watch: str = config.gisaid.logwatch_email
        self.email_base_settings = config.email_base_settings

        self.process = Process(binary=self.gisaid_binary)

    def get_gisaid_samples(self, case_id: str) -> List[GisaidSample]:
        """Get list of Gisaid sample objects."""

        samples: List[models.Sample] = self.status_db.get_sequenced_samples(family_id=case_id)
        gisaid_samples = []
        for sample in samples:
            sample_id: str = sample.internal_id

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

    def get_gisaid_fasta(self, gisaid_samples: List[GisaidSample], case_id: str) -> List[str]:
        """Fetch a fasta files form house keeper for batch upload_results_to_gisaid to gisaid"""
        fasta_file: File = self.housekeeper_api.find_file_in_latest_version(
            case_id=case_id, tags=["consensus"]
        )

        gisaid_delivery_fasta = []
        with open(str(fasta_file.full_path)) as handle:
            fasta_lines = handle.readlines()
            for line in fasta_lines:
                if line[0] == ">":
                    gisaid_delivery_fasta.append(
                        self.get_new_header(old_header=line, samples=gisaid_samples)
                    )
                else:
                    gisaid_delivery_fasta.append(line)
        if not gisaid_delivery_fasta:
            raise InvalidFastaError(message="Empty fasta file")
        return gisaid_delivery_fasta

    def get_new_header(self, samples: List[GisaidSample], old_header: str) -> str:
        for sample in samples:
            sample_id = sample.covv_subm_sample_id
            if old_header.find(sample_id) != -1:
                return f">{sample.covv_virus_name}\n"
        raise FastaSequenceMissingError

    def build_gisaid_fasta(
        self, gisaid_samples: List[GisaidSample], file_name: str, case_id: str
    ) -> Path:
        """Writing a new fasta with headers adjusted for gisaid upload_results_to_gisaid"""

        file: Path = Path(file_name)
        fasta_lines: List[str] = self.get_gisaid_fasta(
            gisaid_samples=gisaid_samples, case_id=case_id
        )

        with open(file, "w") as write_file_obj:
            write_file_obj.writelines(fasta_lines)
        return file

    def get_sample_row(self, gisaid_sample: GisaidSample) -> List[str]:
        """Build row for a sample in the batch upload_results_to_gisaid csv."""

        sample_dict = gisaid_sample.dict()
        return [sample_dict.get(header, "") for header in HEADERS]

    def get_sample_rows(self, gisaid_samples: List[GisaidSample]) -> List[List[str]]:
        """Build sample row list for gisad csv file"""

        sample_rows = []
        for sample in gisaid_samples:
            sample_row: List[str] = self.get_sample_row(gisaid_sample=sample)
            sample_rows.append(sample_row)
        return sample_rows

    def build_gisaid_csv(self, gisaid_samples: List[GisaidSample], file_name: str) -> Path:
        """Build batch upload_results_to_gisaid csv."""

        file: Path = Path(file_name)

        with open(file_name, "w", newline="\n") as gisaid_csv:
            wr = csv.writer(gisaid_csv, delimiter=",")
            wr.writerow(HEADERS)
            sample_rows: List[List[str]] = self.get_sample_rows(gisaid_samples=gisaid_samples)
            wr.writerows(sample_rows)

        return file

    def get_gisaid_log_file_path(self, case_id: str) -> Path:
        """Path for gisaid bundle log"""

        log_file = Path(self.gisaid_log_dir, case_id).with_suffix(".log")
        if not log_file.parent.exists():
            raise ValueError(f"Gisaid log dir: {self.gisaid_log_dir} doesnt exist")
        if not log_file.exists():
            log_file.touch()
        return log_file

    def append_log(self, temp_log: Path, gisaid_log: Path) -> None:
        """appends temp log to gisaid log and delete temp file"""

        with open(str(temp_log.absolute()), "r") as open_temp_log:
            new_log_data: List = json.load(open_temp_log)
            if gisaid_log.stat().st_size != 0:
                with open(str(gisaid_log.absolute()), "r") as open_gisaid_log:
                    old_log_data: List = json.load(open_gisaid_log)
                    new_log_data.extend(old_log_data)

        with open(str(gisaid_log.absolute()), "w") as open_gisaid_log:
            json.dump(new_log_data, open_gisaid_log)
        temp_log.unlink()

    def upload_results_to_gisaid(self, files: UploadFiles) -> None:
        """Load batch data to GISAID using the gisiad cli."""

        temp_log_file = tempfile.NamedTemporaryFile(
            dir=self.gisaid_log_dir, mode="w+", delete=False
        )
        load_call: list = [
            "--logfile",
            temp_log_file.name,
            "CoV",
            "upload",
            "--csv",
            str(files.csv_file.absolute()),
            "--fasta",
            str(files.fasta_file.absolute()),
        ]
        self.process.run_command(parameters=load_call)
        self.append_log(temp_log=Path(temp_log_file.name), gisaid_log=files.log_file)
        temp_log_file.close()
        if self.process.stderr:
            LOG.info(f"gisaid stderr:\n{self.process.stderr}")
        if self.process.stdout:
            LOG.info(f"gisaid stdout:\n{self.process.stdout}")

    def __str__(self):
        return f"GisaidAPI(dry_run: {self.dry_run})"

    def get_accession_numbers(self, log_file: Path) -> Dict[str, str]:
        """parse accession numbers and sample ids from log file"""

        LOG.info("Parsing accesion numbers from log file")
        accession_numbers = {}
        if log_file.stat().st_size != 0:
            with open(str(log_file.absolute())) as log_file:
                log_data = json.load(log_file)
                for log in log_data:
                    if log.get("code") != "epi_isl_id":
                        continue
                    accession_obj = GisaidAccession(log_message=log.get("msg"))
                    accession_numbers[accession_obj.sample_id] = accession_obj.accession_nr

        return accession_numbers

    def get_completion_file_data(
        self, completion_file: Path, completion_data: Dict[str, str]
    ) -> List[List[str]]:
        """Get completion file with accession numbers"""

        new_completion_file_data = [["provnummer", "urvalskriterium", "GISAID_accession"]]
        with open(str(completion_file.absolute()), "r") as file:
            completion_file_reader = csv.DictReader(file, delimiter=",")
            for sample in completion_file_reader:
                sample_id = sample["provnummer"]
                selection_criteria = sample["urvalskriterium"]
                completion_nr = completion_data.get(sample_id, "")
                new_completion_file_data.append([sample_id, selection_criteria, completion_nr])
        return new_completion_file_data

    def update_completion_file(
        self, completion_file: Path, new_completion_file_data: List[List[str]]
    ) -> None:
        """Update completion file with accession numbers"""

        with open(str(completion_file.absolute()), "w", newline="\n") as file:
            LOG.info("writing accession numbers to new completion file")
            writer = csv.writer(file)
            writer.writerows(new_completion_file_data)

    def ensure_log_in_housekeeper(self, case_id: str, file_path: Path, tags: List[str]) -> None:
        """Adding file to housekeeper if it doesnt exist"""

        if not self.housekeeper_api.find_file_in_latest_version(case_id=case_id, tags=tags):
            self.housekeeper_api.add_and_include_file_to_latest_version(
                case_id=case_id, file=file_path, tags=tags
            )

    def get_upload_files(self, gisaid_samples: List[GisaidSample], case_id: str) -> UploadFiles:
        """Get files for upload to gisaid"""
        return UploadFiles(
            csv_file=self.build_gisaid_csv(
                gisaid_samples=gisaid_samples, file_name=f"{case_id}.csv"
            ),
            fasta_file=self.build_gisaid_fasta(
                gisaid_samples=gisaid_samples, file_name=f"{case_id}.fasta", case_id=case_id
            ),
            log_file=self.get_gisaid_log_file_path(case_id=case_id),
        )

    def manage_completion_file_data(self, case_id: str, accession_numbers: Dict[str, str]) -> None:
        """Merging old completion file data with new"""
        completion_file: Optional[File] = self.housekeeper_api.find_file_in_latest_version(
            case_id=case_id, tags=["komplettering"]
        )
        if not completion_file:
            msg = f"completion file missing for bundle {case_id}"
            raise HousekeeperFileMissingError(message=msg)
        new_completion_data: List[List[str]] = self.get_completion_file_data(
            completion_file=completion_file, completion_data=accession_numbers
        )
        self.update_completion_file(
            completion_file=completion_file,
            new_completion_file_data=new_completion_data,
        )

    def unlik_tmp_files(self, files: UploadFiles) -> None:
        """Unlinking tmp files"""
        files.csv_file.unlink()
        files.fasta_file.unlink()

    def upload(self, case_id: str) -> None:
        """Uploading results to gisaid and saving the accession numbers in completion file"""

        gisaid_samples: List[GisaidSample] = self.get_gisaid_samples(case_id=case_id)
        files: UploadFiles = self.get_upload_files(gisaid_samples, case_id)
        accession_numbers: Dict[str, str] = self.get_accession_numbers(log_file=files.log_file)
        if len(accession_numbers) == len(gisaid_samples):
            self.unlik_tmp_files(files=files)
            raise GisaidUploadFailedError(
                message=f"The samples in bundle {case_id} are already uploaded to GISAID and can not be uploaded more "
                f"than once. "
            )

        try:
            self.upload_results_to_gisaid(files=files)
            self.unlik_tmp_files(files=files)
        except Exception as e:
            raise GisaidUploadFailedError(message=str(e))

        self.ensure_log_in_housekeeper(
            case_id=case_id, tags=["gisaid-log"], file_path=files.log_file
        )

        accession_numbers: Dict[str, str] = self.get_accession_numbers(log_file=files.log_file)
        if accession_numbers:
            self.manage_completion_file_data(case_id=case_id, accession_numbers=accession_numbers)

        if len(accession_numbers) != len(gisaid_samples):
            raise AccessionNumerMissingError(
                message=f"Not all samples in the bundle {case_id} have been uploaded to gisaid."
            )
