"""Module for deliver and rsync customer inbox on hasta to customer inbox on caesar"""
import datetime as dt
import logging
import os
from pathlib import Path
from typing import List, Tuple, Optional
import hashlib

from housekeeper.store.models import Bundle

from cg.apps.cgstats.db.models import Version
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.meta.meta import MetaAPI
from cg.meta.rsync.sbatch import RSYNC_COMMAND, ERROR_RSYNC_FUNCTION
from cg.models.cg_config import CGConfig
from cg.models.slurm.sbatch import Sbatch
from cg.store import models

LOG = logging.getLogger(__name__)


class ExternalDataAPI(MetaAPI):
    def __init__(self, config: CGConfig):
        super().__init__(config)
        self.hasta_path: str = config.external.hasta
        self.caesar_path: str = config.external.caesar
        self.base_path: str = config.data_delivery.base_path
        self.account: str = config.data_delivery.account
        self.mail_user: str = config.data_delivery.mail_user
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.customer = None
        self.ticket_id = None

    def create_log_dir(self, dry_run: bool) -> Path:
        timestamp = dt.datetime.now()
        timestamp_str = timestamp.strftime("%y%m%d_%H_%M_%S_%f")
        folder_name = Path("_".join([str(self.ticket_id), timestamp_str]))
        log_dir = Path(self.base_path) / folder_name
        LOG.info("Creating folder: %s", log_dir)
        if dry_run:
            LOG.info("Would have created path %s, but this is a dry run", log_dir)
            return log_dir
        log_dir.mkdir(parents=True, exist_ok=False)
        return log_dir

    def create_source_path(self, raw_path: str, cust_sample_id: str) -> str:
        cust_id_added_to_path = (
            raw_path % self.customer + "/" + str(self.ticket_id) + "/" + cust_sample_id + "/"
        )
        return cust_id_added_to_path

    def create_destination_path(self, raw_path: str, lims_sample_id: str) -> str:
        cust_id_added_to_path = raw_path % self.customer + "/" + lims_sample_id + "/"
        return cust_id_added_to_path

    def download_sample(self, cust_sample_id: str, lims_sample_id: str, dry_run: bool) -> int:
        log_dir: Path = self.create_log_dir(dry_run=dry_run)
        source_path: str = self.create_source_path(
            raw_path=self.caesar_path,
            cust_sample_id=cust_sample_id,
        )
        destination_path: str = self.create_destination_path(
            raw_path=self.hasta_path,
            lims_sample_id=lims_sample_id,
        )
        commands = RSYNC_COMMAND.format(source_path=source_path, destination_path=destination_path)
        error_function = ERROR_RSYNC_FUNCTION.format()
        sbatch_info = {
            "job_name": "_".join([str(self.ticket_id), "rsync_external_data"]),
            "account": self.account,
            "number_tasks": 1,
            "memory": 1,
            "log_dir": log_dir.as_posix(),
            "email": self.mail_user,
            "hours": 24,
            "commands": commands,
            "error": error_function,
        }
        slurm_api = SlurmAPI()
        slurm_api.set_dry_run(dry_run=dry_run)
        sbatch_content: str = slurm_api.generate_sbatch_content(Sbatch.parse_obj(sbatch_info))
        sbatch_path = log_dir / "_".join([str(self.ticket_id), "rsync_external_data.sh"])
        sbatch_number: int = slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        return sbatch_number

    def set_ticket_params(self, ticket_id):
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        self.customer = cases[0].customer.internal_id
        self.ticket_id = ticket_id

    def download_ticket(self, ticket_id: int, dry_run: bool) -> None:
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        self.set_ticket_params(ticket_id=ticket_id)
        for case in cases:
            links = case.links
            for link in links:
                lims_sample_id = link.sample.internal_id
                cust_sample_id = link.sample.name
                sbatch_number = self.download_sample(
                    cust_sample_id=cust_sample_id,
                    lims_sample_id=lims_sample_id,
                    dry_run=dry_run,
                )
                LOG.info(
                    "Downloading sample %s from caesar by submitting sbatch job %s"
                    % (lims_sample_id, sbatch_number)
                )

    def get_all_fastq(self, sample_folder: str) -> List[str]:
        all_fastqs = []
        for leaf in os.listdir(sample_folder):
            abs_path = sample_folder + leaf
            LOG.info("Found file %s inside folder %s" % (abs_path, sample_folder))
            if abs_path.endswith("fastq.gz"):
                all_fastqs.append(abs_path)
        return all_fastqs

    def get_all_paths(self, lims_sample_id: str) -> List[str]:
        fastq_folder: str = self.create_destination_path(
            lims_sample_id=lims_sample_id, raw_path=self.hasta_path
        )
        all_fastq_in_folder: List[str] = self.get_all_fastq(sample_folder=fastq_folder)
        return all_fastq_in_folder

    def create_hk_bundle(
        self, bundle_name: str, dry_run: bool, data_dict: dict
    ) -> Optional[Tuple[Bundle, Version]]:
        if dry_run:
            LOG.info(
                "Would have created bundle %s in housekeeper, but this is dry-run", bundle_name
            )
            return
        bundle_result: Tuple[Bundle, Version] = self.housekeeper_api.add_bundle(
            bundle_data=data_dict
        )
        return bundle_result

    def create_dict(self, name: str) -> dict:
        hk_dict = {
            "name": name,
            "created_at": dt.datetime.now(),
            "expires_at": None,
            "files": [],
        }
        return hk_dict

    def configure_housekeeper(self, ticket_id: int, dry_run: bool) -> None:
        self.set_ticket_params(ticket_id=ticket_id)
        cases = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        for case in cases:
            links = case.links
            for link in links:
                lims_sample_id = link.sample.internal_id
                paths: List[str] = self.get_all_paths(lims_sample_id=lims_sample_id)
                if dry_run:
                    LOG.info(
                        "Would have added %s to housekeeper and linked associated files, but this is dry-run",
                        lims_sample_id,
                    )
                    return
                last_version = self.housekeeper_api.last_version(bundle=lims_sample_id)

                if not last_version:
                    LOG.info("Creating bundle for sample %s in housekeeper", lims_sample_id)
                    hk_dict: dict = self.create_dict(name=lims_sample_id)
                    bundle_result: Tuple[Bundle, Version] = self.create_hk_bundle(
                        bundle_name=lims_sample_id, data_dict=hk_dict, dry_run=dry_run
                    )
                    last_version = bundle_result[1]
                    files = []
                else:
                    files = [
                        tmp.path
                        for tmp in self.housekeeper_api.get_files(
                            bundle=lims_sample_id, tags=["fastq"], version=last_version.id
                        )
                    ]

                for path in paths:
                    if path in files:
                        LOG.info(
                            "Path %s is already linked to bundle %s in housekeeper"
                            % (path, lims_sample_id)
                        )
                        continue

                    LOG.info("Adding path %s to bundle %s in housekeeper" % (path, lims_sample_id))
                    self.housekeeper_api.add_file(
                        path=path, version_obj=last_version, tags=["fastq"]
                    )
                    do_commit = True
                    if os.path.isfile(path + ".md5"):
                        do_commit = check_md5sum(fastq_path=path)
                    else:
                        LOG.info("No md5 file found for file  %s" % path + ".md5")
                    if not do_commit:
                        return
        self.housekeeper_api.commit()
        self.set_to_analyze(cases=cases)

    def set_to_analyze(self, cases):
        for case_obj in cases:
            case_obj.action = "analyze"
            self.status_db.commit()
        LOG.info("Setting all cases to analyze.")


def check_md5sum(fastq_path) -> bool:
    """Checks if there is and md5 file associated with the fastq-file and if so verifies the cheksum"""
    with open(fastq_path, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)
    outp_sum = file_hash.hexdigest()
    with open(fastq_path + ".md5", "r") as md:
        check_sum = extract_md5sum(md.readline())
    if check_sum == outp_sum:
        LOG.info("The md5 file matches the md5sum for file  %s" % fastq_path)
        return True
    else:
        LOG.info("The md5 file does not match the md5sum for file  %s" % fastq_path)
        LOG.info("No cases will be added to housekeeper.")
        return False


def extract_md5sum(first_line: str) -> str:
    """Searches the line for a string matching the length of an md5sum"""
    line_list = first_line.split(" ")
    for element in line_list:
        element = element.strip()
        if len(element) == 32 and "." not in element:
            md5sum = element
            return md5sum
    LOG.info("No valid md5sum found in the .md5 file.")
    return ""
