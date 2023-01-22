import datetime as dt
import logging
from pathlib import Path
from typing import List, Optional

from cg.apps.cgstats.db.models import Version
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants import HK_FASTQ_TAGS
from cg.meta.meta import MetaAPI
from cg.meta.rsync.sbatch import ERROR_RSYNC_FUNCTION, RSYNC_CONTENTS_COMMAND
from cg.models.cg_config import CGConfig
from cg.models.slurm.sbatch import Sbatch
from cg.store import models
from cg.utils.checksum.checksum import check_md5sum, extract_md5sum

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

    def create_log_dir(self, dry_run: bool, ticket: str) -> Path:
        """Creates a directory for log file to be stored"""
        timestamp: dt.datetime = dt.datetime.now()
        timestamp_str: str = timestamp.strftime("%y%m%d_%H_%M_%S_%f")
        folder_name: Path = Path("_".join([ticket, timestamp_str]))
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
        ticket: str,
        cust_sample_id: Optional[str] = "",
    ) -> Path:
        """Returns the path to where the sample files are fetched from"""
        return Path(self.source_path % customer, ticket, cust_sample_id)

    def get_destination_path(self, customer: str, lims_sample_id: Optional[str] = "") -> Path:
        """Returns the path to where the files are to be transferred"""
        return Path(self.destination_path % customer, lims_sample_id)

    def transfer_sample_files_from_source(self, dry_run: bool, ticket: str) -> None:
        """Transfers all sample files, related to given ticket, from source to destination"""
        cust: str = self.status_db.get_customer_id_from_ticket(ticket=ticket)
        log_dir: Path = self.create_log_dir(ticket=ticket, dry_run=dry_run)
        error_function: str = ERROR_RSYNC_FUNCTION.format()
        Path(self.destination_path % cust).mkdir(exist_ok=True)

        command: str = RSYNC_CONTENTS_COMMAND.format(
            source_path=self.get_source_path(customer=cust, ticket=ticket),
            destination_path=self.get_destination_path(customer=cust),
        )
        sbatch_parameters: Sbatch = Sbatch(
            job_name=ticket + self.RSYNC_FILE_POSTFIX,
            account=self.account,
            number_tasks=1,
            memory=1,
            log_dir=str(log_dir),
            email=self.mail_user,
            hours=24,
            commands=command,
            error=error_function,
        )
        self.slurm_api.set_dry_run(dry_run=dry_run)
        sbatch_content: str = self.slurm_api.generate_sbatch_content(
            sbatch_parameters=sbatch_parameters
        )
        sbatch_path: Path = Path(log_dir, ticket + self.RSYNC_FILE_POSTFIX + ".sh")
        self.slurm_api.submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_path)
        LOG.info(
            "The folder {src_path} is now being rsynced to hasta".format(
                src_path=self.get_source_path(customer=cust, ticket=ticket)
            )
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
        """Returns the path of the input file if it does not match its md5sum"""
        if Path(str(fastq_path) + ".md5").exists():
            given_md5sum: str = extract_md5sum(md5sum_file=Path(str(fastq_path) + ".md5"))
            if not check_md5sum(file_path=fastq_path, md5sum=given_md5sum):
                return fastq_path

    def get_available_samples(self, folder: Path, ticket: str) -> List[models.Sample]:
        """Returns the samples from given ticket that are present in the provided folder"""
        available_folders: List[str] = [sample_path.parts[-1] for sample_path in folder.iterdir()]
        available_samples: List[models.Sample] = [
            sample
            for sample in self.status_db.get_samples_from_ticket(ticket=ticket)
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

    def get_failed_fastq_paths(self, fastq_paths_to_add: List[Path]) -> List[Path]:
        failed_sum_paths: List[Path] = []
        for path in fastq_paths_to_add:
            failed_path: Optional[Path] = self.check_fastq_md5sum(path)
            if failed_path:
                failed_sum_paths.append(failed_path)
        return failed_sum_paths

    def get_fastq_paths_to_add(
        self, customer: str, hk_version: Version, lims_sample_id: str
    ) -> List[Path]:
        paths: List[Path] = self.get_all_paths(lims_sample_id=lims_sample_id, customer=customer)
        fastq_paths_to_add: List[Path] = self.housekeeper_api.check_bundle_files(
            file_paths=paths,
            bundle_name=lims_sample_id,
            last_version=hk_version,
            tags=HK_FASTQ_TAGS,
        )
        return fastq_paths_to_add

    def curate_sample_folder(self, cust_name: str, force: bool, sample_folder: Path) -> None:
        """Changes the name of the folder to the internal_id. If force is true replaces any previous folder"""
        customer: models.Customer = self.status_db.customer(internal_id=cust_name)
        customer_folder: Path = sample_folder.parent
        sample: models.Sample = self.status_db.find_samples(
            customer=customer, name=sample_folder.name
        ).first()
        if (sample and not customer_folder.joinpath(sample.internal_id).exists()) or (
            sample and force
        ):
            sample_folder.rename(customer_folder.joinpath(sample.internal_id))
        elif not sample and not self.status_db.sample(sample_folder.name):
            raise Exception(
                f"{sample_folder} is not a sample present in statusdb. Move or remove it to continue"
            )

    def add_transfer_to_housekeeper(
        self, ticket: str, dry_run: bool = False, force: bool = False
    ) -> None:
        """Creates sample bundles in housekeeper and adds the available files corresponding to the ticket to the
        bundle"""
        failed_paths: List[Path] = []
        cust: str = self.status_db.get_customer_id_from_ticket(ticket=ticket)
        destination_folder_path: Path = self.get_destination_path(customer=cust)
        for sample_folder in destination_folder_path.iterdir():
            self.curate_sample_folder(cust_name=cust, sample_folder=sample_folder, force=force)
        available_samples: List[models.Sample] = self.get_available_samples(
            folder=destination_folder_path, ticket=ticket
        )
        cases_to_start: List[dict] = []
        for sample in available_samples:
            cases_to_start.extend(
                self.status_db.cases(sample_id=sample.internal_id, exclude_analysed=True)
            )
            last_version: Version = self.housekeeper_api.get_create_version(
                bundle=sample.internal_id
            )
            fastq_paths_to_add: List[Path] = self.get_fastq_paths_to_add(
                customer=cust, hk_version=last_version, lims_sample_id=sample.internal_id
            )
            self.add_files_to_bundles(
                fastq_paths=fastq_paths_to_add,
                last_version=last_version,
                lims_sample_id=sample.internal_id,
            )
            failed_paths.extend(self.get_failed_fastq_paths(fastq_paths_to_add=fastq_paths_to_add))
        if failed_paths:
            LOG.info(
                "The following samples did not match the given md5sum: "
                + ", ".join([str(path) for path in failed_paths])
            )
            LOG.info("Changes in housekeeper will not be committed and no cases will be added")
            return
        if dry_run:
            LOG.info("No changes will be committed since this is a dry-run")
            return
        self.housekeeper_api.commit()
        for case in cases_to_start:
            self.status_db.set_case_action(case_id=case["internal_id"], action="analyze")
