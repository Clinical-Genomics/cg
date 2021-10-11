"""Module for deliver and rsync customer inbox on hasta to customer inbox on caesar"""
import datetime as dt
import logging
from pathlib import Path
from typing import List, Tuple, Optional

from housekeeper.store.models import Bundle

from cg.apps.cgstats.db.models import Version
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.meta.meta import MetaAPI
from cg.meta.rsync.sbatch import RSYNC_COMMAND, ERROR_RSYNC_FUNCTION
from cg.models.cg_config import CGConfig
from cg.models.slurm.sbatch import Sbatch
from cg.store import models
from cg.meta.transfer.md5sum import check_md5sum, extract_md5sum

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

    def create_log_dir(self, ticket_id: int, dry_run: bool) -> Path:
        """Creates a directory for log file to be stored"""
        timestamp: dt.datetime = dt.datetime.now()
        timestamp_str: str = timestamp.strftime("%y%m%d_%H_%M_%S_%f")
        folder_name: Path = Path("_".join([str(ticket_id), timestamp_str]))
        log_dir: Path = Path(self.base_path) / folder_name
        LOG.info("Creating folder: %s", log_dir)
        if dry_run:
            LOG.info("Would have created path %s, but this is a dry run", log_dir)
            return log_dir
        log_dir.mkdir(parents=True, exist_ok=False)
        return log_dir

    def create_source_path(
        self, raw_path: str, ticket_id: int, customer: str, cust_sample_id: str
    ) -> Path:
        """Returns the path to where the sample files are located on caesar"""
        return Path(raw_path % customer).joinpath(str(ticket_id), cust_sample_id)

    def create_destination_path(self, raw_path: str, customer: str, lims_sample_id: str) -> Path:
        """Returns the path to where the files are to be transferred on hasta"""
        return Path(raw_path % customer).joinpath(lims_sample_id)

    def transfer_sample(
        self, cust_sample_id: str, ticket_id: int, cust: str, lims_sample_id: str, dry_run: bool
    ) -> int:
        """Runs a slurm job to download a sample folder from caesar to hasta. Returns slurm jobid"""
        log_dir: Path = self.create_log_dir(ticket_id=ticket_id, dry_run=dry_run)
        source_path: Path = self.create_source_path(
            raw_path=self.caesar_path,
            ticket_id=ticket_id,
            customer=cust,
            cust_sample_id=cust_sample_id,
        )
        destination_path: Path = self.create_destination_path(
            raw_path=self.hasta_path,
            customer=cust,
            lims_sample_id=lims_sample_id,
        )
        commands: str = RSYNC_COMMAND.format(
            source_path=source_path, destination_path=destination_path
        )
        error_function: str = ERROR_RSYNC_FUNCTION.format()
        sbatch_info = {
            "job_name": "_".join([str(ticket_id), "rsync_external_data"]),
            "account": self.account,
            "number_tasks": 1,
            "memory": 1,
            "log_dir": log_dir.as_posix(),
            "email": self.mail_user,
            "hours": 24,
            "commands": commands,
            "error": error_function,
        }
        slurm_api: SlurmAPI = SlurmAPI()
        slurm_api.set_dry_run(dry_run=dry_run)
        sbatch_content: str = slurm_api.generate_sbatch_content(Sbatch.parse_obj(sbatch_info))
        sbatch_path: Path = log_dir.joinpath(str(ticket_id) + "_rsync_external_data.sh")
        sbatch_number: int = slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        return sbatch_number

    def transfer_sample_files_from_caesar(self, ticket_id: int, dry_run: bool):
        """Transfers all samples, related to given ticket, from caesar to hasta."""
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        cust: str = self.status_db.get_customer_id_from_ticket(ticket_id=ticket_id)
        for case in cases:
            links = case.links
            for link in links:
                lims_sample_id: str = link.sample.internal_id
                cust_sample_id: str = link.sample.name
                sbatch_number: int = self.transfer_sample(
                    ticket_id=ticket_id,
                    cust=cust,
                    cust_sample_id=cust_sample_id,
                    lims_sample_id=lims_sample_id,
                    dry_run=dry_run,
                )
                LOG.info(
                    "Downloading sample %s from caesar by submitting sbatch job %s"
                    % (lims_sample_id, sbatch_number)
                )

    def get_all_fastq(self, sample_folder: Path) -> List[Path]:
        """Returns a list of all fastq.gz files in given folder."""
        all_fastqs: List[Path] = []
        for leaf in sample_folder.iterdir():
            abs_path: Path = sample_folder.joinpath(leaf)
            LOG.info("Found file %s inside folder %s" % (str(abs_path), sample_folder))
            if abs_path.suffixes == [".fastq", ".gz"]:
                all_fastqs.append(abs_path)
        return all_fastqs

    def get_all_paths(self, lims_sample_id: str, customer: str) -> List[Path]:
        """Returns the paths of all fastq files associated to the sample."""
        fastq_folder: Path = self.create_destination_path(
            lims_sample_id=lims_sample_id, customer=customer, raw_path=self.hasta_path
        )
        all_fastq_in_folder: List[Path] = self.get_all_fastq(sample_folder=fastq_folder)
        return all_fastq_in_folder

    def create_hk_bundle(
        self, bundle_name: str, dry_run: bool, data_dict: dict
    ) -> Optional[Tuple[Bundle, Version]]:
        """Creates and returns a housekeeper bundle and the new version."""
        if dry_run:
            LOG.info(
                "Would have created bundle %s in housekeeper, but this is dry-run", bundle_name
            )
            return
        bundle_result: Tuple[Bundle, Version] = self.housekeeper_api.add_bundle(
            bundle_data=data_dict
        )
        return bundle_result

    def check_bundle_fastq_files(
        self, fastq_paths: List[Path], lims_sample_id: str, last_version: Version
    ) -> List[Path]:
        """Checks if any of the fastq files are already added. Returns a list of files that should be added."""
        for file in self.housekeeper_api.get_files(
            bundle=lims_sample_id, tags=["fastq"], version=last_version.id
        ):
            if Path(file.path) in fastq_paths:
                fastq_paths.remove(Path(file.path))
                LOG.info(
                    "Path %s is already linked to bundle %s in housekeeper"
                    % (file.path, lims_sample_id)
                )
        return fastq_paths

    def add_files_to_bundles(
        self, fastq_paths: List[Path], last_version: Version, lims_sample_id: str
    ) -> bool:
        """Adds the given files to the the hk-bundle if the md5sum matches or no md5sum is provided."""
        for path in fastq_paths:
            do_commit: bool = True
            if Path(str(path) + ".md5").exists():
                given_md5sum: str = extract_md5sum(md5sum_file=Path(str(path) + ".md5"))
                do_commit: bool = check_md5sum(file_path=path, md5sum=given_md5sum)
            else:
                LOG.info("No md5 file found for file  %s" % path + ".md5")
            if do_commit:
                LOG.info("Adding path %s to bundle %s in housekeeper" % (path, lims_sample_id))
                self.housekeeper_api.add_file(path=path, version_obj=last_version, tags=["fastq"])
            else:
                return False
        return True

    def configure_housekeeper(self, ticket_id: int, dry_run: bool = False) -> None:
        """Creates sample bundles in housekeeper and adds the files corresponding to the ticket to the bundle."""
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        cust: str = self.status_db.get_customer_id_from_ticket(ticket_id=ticket_id)
        for case in cases:
            links = case.links
            for link in links:
                lims_sample_id: str = link.sample.internal_id
                paths: List[Path] = self.get_all_paths(lims_sample_id=lims_sample_id, customer=cust)
                if dry_run:
                    LOG.info(
                        "Would have added %s to housekeeper and linked associated files, but this is dry-run",
                        lims_sample_id,
                    )
                    return
                last_version: Version = self.housekeeper_api.get_create_version(
                    lims_sample_id=lims_sample_id
                )
                fastq_paths_to_add: List[Path] = self.check_bundle_fastq_files(
                    fastq_paths=paths, lims_sample_id=lims_sample_id, last_version=last_version
                )
                if not self.add_files_to_bundles(
                    fastq_paths=fastq_paths_to_add,
                    last_version=last_version,
                    lims_sample_id=lims_sample_id,
                ):
                    LOG.info("No cases will be added to housekeeper.")
                    return
                LOG.info("The md5 files match the md5sum for sample {}".format(lims_sample_id))
        self.housekeeper_api.commit()
        self.status_db.set_cases_to_analyze(cases=[case.internal_id for case in cases])
