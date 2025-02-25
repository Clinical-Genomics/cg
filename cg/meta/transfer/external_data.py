import datetime as dt
import logging
from pathlib import Path

from housekeeper.store.models import Version

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants import HK_FASTQ_TAGS, FileExtensions
from cg.constants.constants import CaseActions
from cg.meta.meta import MetaAPI
from cg.meta.transfer.utils import are_all_fastq_valid
from cg.models.cg_config import CGConfig
from cg.models.slurm.sbatch import Sbatch
from cg.services.deliver_files.rsync.sbatch import (
    ERROR_RSYNC_FUNCTION,
    RSYNC_CONTENTS_COMMAND,
)
from cg.store.models import Case, Customer, Sample
from cg.utils.files import get_files_matching_pattern

LOG = logging.getLogger(__name__)


class ExternalDataAPI(MetaAPI):
    def __init__(self, config: CGConfig):
        super().__init__(config)
        self.account: str = config.data_delivery.account
        self.base_path: str = config.data_delivery.base_path
        self.customer_id: str | None = None
        self.destination_path_stub: str = config.external.hasta
        self.dry_run: bool = False
        self.force: bool = False
        self.mail_user: str = config.data_delivery.mail_user
        self.RSYNC_FILE_POSTFIX: str = "_rsync_external_data"
        self.slurm_api: SlurmAPI = SlurmAPI()
        self.source_path: str = config.external.caesar
        self.ticket: str | None = None

    def _set_parameters(self, ticket: str, dry_run: bool, force: bool = False):
        """Set the parameters for the API."""
        self.ticket = ticket
        self.dry_run = dry_run
        self.force = force
        self.customer_id = self.status_db.get_customer_id_from_ticket(ticket=self.ticket)

    def _create_log_dir(self) -> Path:
        """Creates a directory for log file to be stored"""
        timestamp: str = dt.datetime.now().strftime("%y%m%d_%H_%M_%S_%f")
        folder_name = Path("_".join([self.ticket, timestamp]))
        log_dir: Path = Path(self.base_path, folder_name)
        LOG.debug(f"Creating folder: {log_dir}")
        if self.dry_run:
            LOG.info(f"Would have created path {log_dir}, but this is a dry run")
            return log_dir
        log_dir.mkdir(parents=True, exist_ok=False)
        return log_dir

    def _get_customer_source_path(self) -> Path:
        """Returns the path to where the sample files are fetched from."""
        return Path(self.source_path % self.customer_id, self.ticket)

    def _get_destination_path(self, lims_sample_id: str | None = "") -> Path:
        """Returns the path to where the files are to be transferred."""
        return Path(self.destination_path_stub % self.customer_id, lims_sample_id)

    def transfer_sample_files_from_source(self, ticket: str, dry_run: bool = False) -> None:
        """Transfers all sample files on given ticket, from source to destination."""
        self._set_parameters(ticket=ticket, dry_run=dry_run)
        LOG.debug(f"Transferring files for ticket {self.ticket} of customer {self.customer_id}")
        log_dir: Path = self._create_log_dir()
        self._get_destination_path().mkdir(exist_ok=True)

        command: str = RSYNC_CONTENTS_COMMAND.format(
            source_path=self._get_customer_source_path(),
            destination_path=self._get_destination_path(),
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
            error=ERROR_RSYNC_FUNCTION.format(),
        )
        self.slurm_api.set_dry_run(dry_run=dry_run)
        sbatch_content: str = self.slurm_api.generate_sbatch_content(sbatch_parameters)
        sbatch_path = Path(log_dir, self.ticket + self.RSYNC_FILE_POSTFIX + FileExtensions.SH)
        self.slurm_api.submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_path)
        LOG.info(
            f"The folder {self._get_customer_source_path().as_posix()} is now being Rsynced to destination"
        )

    def _curate_sample_folder(self, sample_folder: Path) -> None:
        """
        Changes the name of the folder to the sample internal_id. If force is set to True,
        replaces any previous folder.
        Raises:
            Exception if the sample from the folder is not present in StatusDB.
        """
        customer: Customer = self.status_db.get_customer_by_internal_id(self.customer_id)
        customer_folder: Path = sample_folder.parent
        sample_by_name: Sample | None = self.status_db.get_sample_by_customer_and_name(
            customer_entry_id=[customer.id], sample_name=sample_folder.name
        )
        sample_by_id: Sample | None = self.status_db.get_sample_by_internal_id(sample_folder.name)
        if not (sample_by_name or sample_by_id):
            raise Exception(
                f"{sample_folder} is not a sample present in StatusDB. "
                "Move or remove it to continue"
            )
        sample: Sample = sample_by_name or sample_by_id
        new_folder: Path = customer_folder.joinpath(sample.internal_id)
        if not new_folder.exists() or self.force:
            if self.dry_run:
                LOG.debug(f"Dry-run: Would have renamed folder {sample_folder} to {new_folder}")
                return
            sample_folder.rename(new_folder)

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
        destination_folder_path: Path = self._get_destination_path()
        LOG.debug(f"Checking available samples in {destination_folder_path}")
        for sample_folder in destination_folder_path.iterdir():
            self._curate_sample_folder(sample_folder=sample_folder)
        available_sample_ids: list[str] = self._get_sample_ids_from_folder(destination_folder_path)
        return available_sample_ids

    def _get_fastq_paths_to_add(self, sample_id: str) -> list[Path]:
        """Return the paths of fastq files that have not been added to the Housekeeper bundle."""
        sample_folder: Path = self._get_destination_path(sample_id)
        LOG.debug(f"Checking fastq files in {sample_folder}")
        file_paths: list[Path] = [
            sample_folder.joinpath(path)
            for path in get_files_matching_pattern(
                directory=sample_folder, pattern=f"*{FileExtensions.FASTQ_GZ}"
            )
        ]
        LOG.debug(f"Found {len(file_paths)} fastq files for sample {sample_id}")
        hk_version: Version = self.housekeeper_api.get_or_create_version(bundle_name=sample_id)
        fastq_paths_to_add: list[Path] = self.housekeeper_api.check_bundle_files(
            file_paths=file_paths,
            bundle_name=sample_id,
            last_version=hk_version,
            tags=HK_FASTQ_TAGS,
        )
        LOG.debug(f"{len(fastq_paths_to_add)} files are not yet in Housekeeper for {sample_id}")
        return fastq_paths_to_add

    def _add_and_include_files_to_bundles(
        self, fastq_paths: list[Path], lims_sample_id: str
    ) -> None:
        """Add the given fastq files to the the Housekeeper bundle."""
        if self.dry_run:
            LOG.info(f"No files will be added for sample {lims_sample_id} since this is a dry-run")
            return
        for path in fastq_paths:
            LOG.info(f"Adding path {path} to bundle {lims_sample_id} in Housekeeper")
            self.housekeeper_api.add_and_include_file_to_latest_version(
                bundle_name=lims_sample_id, file=path, tags=HK_FASTQ_TAGS
            )

    def _start_cases(self, cases: list[Case] | None) -> None:
        """Starts the cases that have not been analysed."""
        if self.dry_run:
            LOG.info("No cases will be started since this is a dry-run")
            return
        if not cases:
            LOG.info("No cases to start")
            return
        for case in cases:
            self.status_db.set_case_action(
                case_internal_id=case.internal_id, action=CaseActions.ANALYZE
            )
            LOG.info(f"Case {case.internal_id} has been set to '{CaseActions.ANALYZE}'")

    def add_external_data_to_housekeeper(
        self, ticket: str, dry_run: bool = False, force: bool = False
    ) -> None:
        """
        Add and include available ticket fastq files to a Housekeeper bundle if they are not
        corrupted and start cases associated with the ticket.
        """
        self._set_parameters(ticket=ticket, dry_run=dry_run, force=force)
        LOG.info(
            f"Adding fastq files to Housekeeper for ticket {self.ticket} of customer {self.customer_id}"
        )
        available_sample_ids: list[str] = self._get_available_sample_ids()
        for sample_id in available_sample_ids:
            fastq_paths_to_add: list[Path] = self._get_fastq_paths_to_add(sample_id=sample_id)
            if not fastq_paths_to_add:
                LOG.info(f"Did not find any fastq file to add for sample {sample_id}, skipping")
                continue
            if are_all_fastq_valid(fastq_paths=fastq_paths_to_add):
                self._add_and_include_files_to_bundles(
                    fastq_paths=fastq_paths_to_add,
                    lims_sample_id=sample_id,
                )
                self._start_cases(
                    cases=self.status_db.get_not_analysed_cases_by_sample_internal_id(
                        sample_internal_id=sample_id
                    )
                )
            else:
                LOG.warning(
                    f"Some files in {sample_id} did not match the given md5sum."
                    " Changes in Housekeeper will not be committed and no cases will be started"
                )
