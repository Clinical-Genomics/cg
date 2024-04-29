import datetime as dt
import logging
from pathlib import Path

from housekeeper.store.models import Version

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants import HK_FASTQ_TAGS
from cg.meta.meta import MetaAPI
from cg.meta.rsync.sbatch import ERROR_RSYNC_FUNCTION, RSYNC_CONTENTS_COMMAND
from cg.models.cg_config import CGConfig
from cg.models.slurm.sbatch import Sbatch
from cg.store.models import Case, Customer, Sample
from cg.utils.checksum.checksum import check_md5sum, extract_md5sum

LOG = logging.getLogger(__name__)


class ExternalDataAPI(MetaAPI):
    def __init__(self, config: CGConfig):
        super().__init__(config)
        self.account: str = config.data_delivery.account
        self.base_path: str = config.data_delivery.base_path
        self.customer_id: str | None = None
        self.destination_path: str = config.external.hasta
        self.dry_run: bool | None = None
        self.force: bool | None = None
        self.mail_user: str = config.data_delivery.mail_user
        self.RSYNC_FILE_POSTFIX: str = "_rsync_external_data"
        self.slurm_api: SlurmAPI = SlurmAPI()
        self.source_path: str = config.external.caesar
        self.ticket: str | None = None

    def _set_parameters(self, ticket: str, dry_run: bool, force: bool | None = False):
        """Set the parameters for the API."""
        self.ticket = ticket
        self.dry_run = dry_run
        self.force = force
        self.customer_id = self.status_db.get_customer_id_from_ticket(ticket=self.ticket)

    def create_log_dir(self) -> Path:
        """Creates a directory for log file to be stored"""
        timestamp: dt.datetime = dt.datetime.now()
        timestamp_str: str = timestamp.strftime("%y%m%d_%H_%M_%S_%f")
        folder_name: Path = Path("_".join([self.ticket, timestamp_str]))
        log_dir: Path = Path(self.base_path, folder_name)
        LOG.info(f"Creating folder: {log_dir}")
        if self.dry_run:
            LOG.info(f"Would have created path {log_dir}, but this is a dry run")
            return log_dir
        log_dir.mkdir(parents=True, exist_ok=False)
        return log_dir

    def get_source_path(self, cust_sample_id: str | None = "") -> Path:
        """Returns the path to where the sample files are fetched from"""
        return Path(self.source_path % self.customer_id, self.ticket, cust_sample_id)

    def get_destination_path(self, lims_sample_id: str | None = "") -> Path:
        """Returns the path to where the files are to be transferred"""
        return Path(self.destination_path % self.customer_id, lims_sample_id)

    def transfer_sample_files_from_source(self, dry_run: bool, ticket: str) -> None:
        """Transfers all sample files, related to given ticket, from source to destination"""
        self._set_parameters(ticket=ticket, dry_run=dry_run)
        log_dir: Path = self.create_log_dir()
        error_function: str = ERROR_RSYNC_FUNCTION.format()
        Path(self.destination_path % self.customer_id).mkdir(exist_ok=True)

        command: str = RSYNC_CONTENTS_COMMAND.format(
            source_path=self.get_source_path(),
            destination_path=self.get_destination_path(),
        )
        sbatch_parameters = Sbatch(
            job_name=self.ticket + self.RSYNC_FILE_POSTFIX,
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
        sbatch_path: Path = Path(log_dir, self.ticket + self.RSYNC_FILE_POSTFIX + ".sh")
        self.slurm_api.submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_path)
        LOG.info(
            "The folder {src_path} is now being rsynced to hasta".format(
                src_path=self.get_source_path()
            )
        )

    def get_all_fastq(self, sample_folder: Path) -> list[Path]:
        """Returns a list of all fastq.gz files in given folder"""
        all_fastqs: list[Path] = []
        for leaf in sample_folder.glob("*fastq.gz"):
            abs_path: Path = sample_folder.joinpath(leaf)
            LOG.info(f"Found file {str(abs_path)} inside folder {sample_folder}")
            all_fastqs.append(abs_path)
        return all_fastqs

    def get_all_paths(self, lims_sample_id: str) -> list[Path]:
        """Returns the paths of all fastq files associated to the sample"""
        fastq_folder: Path = self.get_destination_path(lims_sample_id=lims_sample_id)
        all_fastq_in_folder: list[Path] = self.get_all_fastq(sample_folder=fastq_folder)
        return all_fastq_in_folder

    def check_fastq_md5sum(self, fastq_path) -> Path | None:
        """Returns the path of the input file if it does not match its md5sum"""
        if Path(str(fastq_path) + ".md5").exists():
            given_md5sum: str = extract_md5sum(md5sum_file=Path(str(fastq_path) + ".md5"))
            if not check_md5sum(file_path=fastq_path, md5sum=given_md5sum):
                return fastq_path

    def add_files_to_bundles(
        self, fastq_paths: list[Path], last_version: Version, lims_sample_id: str
    ):
        """Adds the given fastq files to the hk-bundle"""
        for path in fastq_paths:
            LOG.info(f"Adding path {path} to bundle {lims_sample_id} in housekeeper")
            self.housekeeper_api.add_file(
                path=path.as_posix(), version_obj=last_version, tags=HK_FASTQ_TAGS
            )

    def get_failed_fastq_paths(self, fastq_paths_to_add: list[Path]) -> list[Path]:
        failed_sum_paths: list[Path] = []
        for path in fastq_paths_to_add:
            failed_path: Path | None = self.check_fastq_md5sum(path)
            if failed_path:
                failed_sum_paths.append(failed_path)
        return failed_sum_paths

    def get_fastq_paths_to_add(self, hk_version: Version, lims_sample_id: str) -> list[Path]:
        paths: list[Path] = self.get_all_paths(lims_sample_id=lims_sample_id)
        fastq_paths_to_add: list[Path] = self.housekeeper_api.check_bundle_files(
            file_paths=paths,
            bundle_name=lims_sample_id,
            last_version=hk_version,
            tags=HK_FASTQ_TAGS,
        )
        return fastq_paths_to_add

    def curate_sample_folder(self, sample_folder: Path) -> None:
        """Changes the name of the folder to the internal_id."""
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=self.customer_id
        )
        customer_folder: Path = sample_folder.parent
        sample: Sample = self.status_db.get_sample_by_customer_and_name(
            customer_entry_id=[customer.id], sample_name=sample_folder.name
        )
        if (sample and not customer_folder.joinpath(sample.internal_id).exists()) or (
            sample and self.force
        ):
            sample_folder.rename(customer_folder.joinpath(sample.internal_id))
        elif not sample and not self.status_db.get_sample_by_internal_id(sample_folder.name):
            raise Exception(
                f"{sample_folder} is not a sample present in statusdb. Move or remove it to continue"
            )

    def _get_sample_ids_from_folder(self, folder: Path) -> list[str]:
        """Returns the valid samples present in the provided folder."""
        available_folders: list[str] = [sample_path.name for sample_path in folder.iterdir()]
        available_sample_ids: list[str] = [
            sample.internal_id
            for sample in self.status_db.get_samples_from_ticket(ticket=self.ticket)
            if sample.internal_id in available_folders or sample.name in available_folders
        ]
        return available_sample_ids

    def _get_available_sample_ids(self) -> list[str]:
        """Return a list of samples available for adding to Housekeeper."""
        destination_folder_path: Path = self.get_destination_path()
        for sample_folder in destination_folder_path.iterdir():
            self.curate_sample_folder(sample_folder=sample_folder)
        available_sample_ids: list[str] = self._get_sample_ids_from_folder(destination_folder_path)
        return available_sample_ids

    def add_transfer_to_housekeeper(
        self, ticket: str, dry_run: bool = False, force: bool = False
    ) -> None:
        """
        Create sample bundles in housekeeper and add the available files corresponding to the ticket
        to the bundle. If force is True, replace any previous folder.
        """
        self._set_parameters(ticket=ticket, dry_run=dry_run, force=force)
        failed_paths: list[Path] = []
        available_sample_ids: list[str] = self._get_available_sample_ids()
        cases_to_start: list[Case] = []
        for sample_id in available_sample_ids:
            cases_to_start.extend(
                self.status_db.get_not_analysed_cases_by_sample_internal_id(
                    sample_internal_id=sample_id
                )
            )
            last_version: Version = self.housekeeper_api.get_or_create_version(
                bundle_name=sample_id
            )
            fastq_paths_to_add: list[Path] = self.get_fastq_paths_to_add(
                hk_version=last_version, lims_sample_id=sample_id
            )
            self.add_files_to_bundles(
                fastq_paths=fastq_paths_to_add,
                last_version=last_version,
                lims_sample_id=sample_id,
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
            self.status_db.set_case_action(case_internal_id=case.internal_id, action="analyze")
