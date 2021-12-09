"""Module for deliver and rsync customer inbox on hasta to customer inbox on caesar"""
import datetime as dt
import itertools
import logging
from pathlib import Path
from typing import List, Tuple, Optional

from housekeeper.store.models import Bundle

from cg.apps.cgstats.db.models import Version
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.meta.meta import MetaAPI
from cg.meta.rsync.sbatch import RSYNC_CONTENTS_COMMAND, ERROR_RSYNC_FUNCTION
from cg.models.cg_config import CGConfig
from cg.models.slurm.sbatch import Sbatch
from cg.store import models
from cg.meta.transfer.md5sum import check_md5sum, extract_md5sum
from cg.constants import HK_FASTQ_TAGS

LOG = logging.getLogger(__name__)


class ExternalDataAPI(MetaAPI):
    def __init__(self, config: CGConfig):
        super().__init__(config)
        self.destination_path: str = config.external.hasta
        self.source_path: str = config.external.caesar
        self.base_path: str = config.data_delivery.base_path
        self.account: str = config.data_delivery.account
        self.mail_user: str = config.data_delivery.mail_user
        self.slurm_api: SlurmAPI = SlurmAPI()
        self.RSYNC_FILE_POSTFIX: str = "_rsync_external_data"

    def create_log_dir(self, dry_run: bool, ticket_id: int) -> Path:
        """Creates a directory for log file to be stored"""
        timestamp: dt.datetime = dt.datetime.now()
        timestamp_str: str = timestamp.strftime("%y%m%d_%H_%M_%S_%f")
        folder_name: Path = Path("_".join([str(ticket_id), timestamp_str]))
        log_dir: Path = Path(self.base_path, folder_name)
        LOG.info("Creating folder: %s", log_dir)
        if dry_run:
            LOG.info("Would have created path %s, but this is a dry run", log_dir)
            return log_dir
        log_dir.mkdir(parents=True, exist_ok=False)
        return log_dir

    def get_source_path(
        self,
        customer: str,
        ticket_id: int,
        cust_sample_id: Optional[str] = "",
    ) -> Path:
        """Returns the path to where the sample files are fetched from"""
        return Path(self.source_path % customer, str(ticket_id), cust_sample_id)

    def get_destination_path(self, customer: str, lims_sample_id: Optional[str] = "") -> Path:
        """Returns the path to where the files are to be transferred"""
        return Path(self.destination_path % customer, lims_sample_id)

    def transfer_sample_files_from_source(self, dry_run: bool, ticket_id: int) -> None:
        """Transfers all sample files, related to given ticket, from source to destination"""
        cust: str = self.status_db.get_customer_id_from_ticket(ticket_id=ticket_id)
        available_samples: List[models.Sample] = self.get_available_samples(
            folder=self.get_source_path(customer=cust, ticket_id=ticket_id),
            ticket_id=ticket_id,
        )
        log_dir: Path = self.create_log_dir(ticket_id=ticket_id, dry_run=dry_run)
        error_function: str = ERROR_RSYNC_FUNCTION.format()
        Path(self.destination_path % cust).mkdir(exist_ok=True)

        commands: str = "".join(
            [
                RSYNC_CONTENTS_COMMAND.format(
                    source_path=self.get_source_path(
                        cust_sample_id=sample.name, customer=cust, ticket_id=ticket_id
                    ),
                    destination_path=self.get_destination_path(
                        customer=cust, lims_sample_id=sample.internal_id
                    ),
                )
                for sample in available_samples
            ]
        )
        sbatch_info = {
            "job_name": str(ticket_id) + self.RSYNC_FILE_POSTFIX,
            "account": self.account,
            "number_tasks": 1,
            "memory": 1,
            "log_dir": str(log_dir),
            "email": self.mail_user,
            "hours": 24,
            "commands": commands,
            "error": error_function,
        }
        self.slurm_api.set_dry_run(dry_run=dry_run)
        sbatch_content: str = self.slurm_api.generate_sbatch_content(Sbatch.parse_obj(sbatch_info))
        sbatch_path: Path = Path(log_dir, str(ticket_id) + self.RSYNC_FILE_POSTFIX + ".sh")
        self.slurm_api.submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_path)
        LOG.info(msg=[sample.name for sample in available_samples])
        LOG.info(
            "The transfer of the {numb} samples above has begun".format(numb=len(available_samples))
        )

    def get_all_fastq(self, sample_folder: Path) -> List[Path]:
        """Returns a list of all fastq.gz files in given folder"""
        all_fastqs: List[Path] = []
        for leaf in sample_folder.glob("*fastq.gz"):
            abs_path: Path = sample_folder.joinpath(leaf)
            LOG.info("Found file %s inside folder %s" % (str(abs_path), sample_folder))
            all_fastqs.append(abs_path)
        return all_fastqs

    def get_all_paths(self, customer: str, lims_sample_id: str) -> List[Path]:
        """Returns the paths of all fastq files associated to the sample"""
        fastq_folder: Path = self.get_destination_path(
            lims_sample_id=lims_sample_id, customer=customer
        )
        all_fastq_in_folder: List[Path] = self.get_all_fastq(sample_folder=fastq_folder)
        return all_fastq_in_folder

    def check_fastq_md5sum(self, fastq_path) -> Optional[Path]:
        if Path(str(fastq_path) + ".md5").exists():
            given_md5sum: str = extract_md5sum(md5sum_file=Path(str(fastq_path) + ".md5"))
            if not check_md5sum(file_path=fastq_path, md5sum=given_md5sum):
                return fastq_path

    def get_available_samples(self, folder: Path, ticket_id: int) -> List[models.Sample]:
        """Returns the samples from given ticket that are present in the provided folder"""
        available_folders: List[str] = [sample_path.parts[-1] for sample_path in folder.iterdir()]
        available_samples: List[models.Sample] = [
            sample
            for sample in self.status_db.get_samples_from_ticket(ticket_id=ticket_id)
            if sample.internal_id in available_folders or sample.name in available_folders
        ]
        return available_samples

    def add_files_to_bundles(
        self, fastq_paths: List[Path], last_version: Version, lims_sample_id: str
    ):
        """Adds the given fastq files to the the hk-bundle"""
        for path in fastq_paths:
            LOG.info("Adding path %s to bundle %s in housekeeper" % (path, lims_sample_id))
            self.housekeeper_api.add_file(path=path, version_obj=last_version, tags=HK_FASTQ_TAGS)

    def add_transfer_to_housekeeper(self, ticket_id: int, dry_run: bool = False) -> None:
        """Creates sample bundles in housekeeper and adds the files corresponding to the ticket to the bundle"""
        failed_files: List[Path] = []
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        cust: str = self.status_db.get_customer_id_from_ticket(ticket_id=ticket_id)
        for case in cases:
            links = case.links
            for link in links:
                lims_sample_id: str = link.sample.internal_id
                paths: List[Path] = self.get_all_paths(lims_sample_id=lims_sample_id, customer=cust)
                last_version: Version = self.housekeeper_api.get_create_version(
                    bundle=lims_sample_id
                )
                fastq_paths_to_add: List[Path] = self.housekeeper_api.check_bundle_files(
                    file_paths=paths,
                    bundle_name=lims_sample_id,
                    last_version=last_version,
                    tags=HK_FASTQ_TAGS,
                )
                failed_sums: List[Path] = []
                for file in fastq_paths_to_add:
                    pass_check = self.check_fastq_md5sum(file)
                    if pass_check:
                        failed_sums.append(pass_check)
                failed_files.extend(failed_sums)
                self.add_files_to_bundles(
                    fastq_paths=fastq_paths_to_add,
                    last_version=last_version,
                    lims_sample_id=lims_sample_id,
                )
                LOG.info("The md5 files match the md5sum for sample {}".format(lims_sample_id))
        if failed_files:
            LOG.info("Changes in housekeeper will not be committed and no cases will be added")
            return
        if dry_run:
            LOG.info("No changes will be committed since this is a dry-run")
            return
        self.housekeeper_api.commit()
        for case in cases:
            self.status_db.set_case_action(case_id=case.internal_id, action="analyze")
