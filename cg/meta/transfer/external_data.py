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
from cg.store.models import Customer, Sample
from cg.utils.checksum.checksum import is_md5sum_correct

LOG = logging.getLogger(__name__)


def are_all_fastq_valid(fastq_paths: list[Path]) -> bool:
    """Return True if all fastq files of a given sample pass md5 checksum."""
    are_all_valid: bool = True
    for path in fastq_paths:
        if is_md5sum_correct(path):
            are_all_valid = False
            LOG.warning(f"Sample {path} did not match the given md5sum")
    return are_all_valid


def get_all_fastq(sample_folder: Path) -> list[Path]:
    """Returns a list of all fastq.gz files in given folder."""
    all_fastqs: list[Path] = []
    for leaf in sample_folder.glob("*fastq.gz"):
        abs_path: Path = sample_folder.joinpath(leaf)
        LOG.info(f"Found file {str(abs_path)} inside folder {sample_folder}")
        all_fastqs.append(abs_path)
    return all_fastqs


class ExternalDataAPI(MetaAPI):
    """Base class for APIs handling external data."""

    def __init__(self, config: CGConfig, ticket: str, dry_run: bool = False):
        super().__init__(config)
        self.customer_id: str = self.status_db.get_customer_id_from_ticket(ticket=ticket)
        self._destination_path: str = config.external.hasta
        self.dry_run: bool = dry_run
        self.ticket: str = ticket

    def get_destination_path(self, lims_sample_id: str | None = "") -> Path:
        """Returns the path to where the files are to be transferred."""
        return Path(self._destination_path % self.customer_id, lims_sample_id)


class TransferExternalDataAPI(ExternalDataAPI):
    """API for transferring external data from Caesar to Hasta."""

    def __init__(self, config: CGConfig, ticket: str, dry_run: bool = False):
        super().__init__(config, ticket, dry_run)
        self.account: str = config.data_delivery.account
        self.base_path: str = config.data_delivery.base_path
        self.mail_user: str = config.data_delivery.mail_user
        self.slurm_api: SlurmAPI = SlurmAPI()
        self.source_path: str = config.external.caesar
        self.RSYNC_FILE_POSTFIX: str = "_rsync_external_data"

    def get_source_path(self, sample_id: str | None = "") -> Path:
        """Returns the path from where the sample files are fetched."""
        return Path(self.source_path % self.customer_id, self.ticket, sample_id)

    def create_log_dir(self) -> Path:
        """Creates a directory for log file to be stored."""
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

    def transfer_sample_files_from_source(self) -> None:
        """Transfers all sample files, related to given ticket, from source to destination."""
        log_dir: Path = self.create_log_dir()
        error_function: str = ERROR_RSYNC_FUNCTION.format()
        Path(self._destination_path % self.customer_id).mkdir(exist_ok=True)

        command: str = RSYNC_CONTENTS_COMMAND.format(
            source_path=self.get_source_path(),
            destination_path=self.get_destination_path(),
        )
        sbatch_parameters: Sbatch = Sbatch(
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
        self.slurm_api.set_dry_run(dry_run=self.dry_run)
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


class AddExternalDataAPI(ExternalDataAPI):
    """API for adding external data to Housekeeper."""

    def __init__(self, config: CGConfig, ticket: str, dry_run: bool = False, force: bool = False):
        super().__init__(config, ticket, dry_run)
        self.force: bool = force

    def curate_sample_folder(self, sample_folder: Path) -> None:
        """
        Changes the name of the folder to the sample internal_id. If force is set to True,
        replaces any previous folder.
        """
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

    def get_sample_ids_from_folder(self, folder: Path) -> list[str]:
        """Returns the samples present in the provided folder."""
        available_folders: list[str] = [sample_path.name for sample_path in folder.iterdir()]
        available_sample_ids: list[str] = [
            sample.internal_id
            for sample in self.status_db.get_samples_from_ticket(ticket=self.ticket)
            if sample.internal_id in available_folders or sample.name in available_folders
        ]
        return available_sample_ids

    def get_available_sample_ids(self) -> list[str]:
        """Return a list of samples available for adding to Housekeeper."""
        destination_folder_path: Path = self.get_destination_path()
        for sample_folder in destination_folder_path.iterdir():
            self.curate_sample_folder(sample_folder=sample_folder)
        available_sample_ids: list[str] = self.get_sample_ids_from_folder(
            folder=destination_folder_path
        )
        return available_sample_ids

    def get_fastq_paths_to_add(self, lims_sample_id: str) -> list[Path]:
        """Return the paths of fastq files that have not been to the Housekeeper bundle."""
        hk_version: Version = self.housekeeper_api.get_or_create_version(bundle_name=lims_sample_id)
        paths: list[Path] = get_all_fastq(sample_folder=self.get_destination_path(lims_sample_id))
        fastq_paths_to_add: list[Path] = self.housekeeper_api.check_bundle_files(
            file_paths=paths,
            bundle_name=lims_sample_id,
            last_version=hk_version,
            tags=HK_FASTQ_TAGS,
        )
        return fastq_paths_to_add

    def add_and_include_files_to_bundles(self, fastq_paths: list[Path], lims_sample_id: str):
        """Add the given fastq files to the the hk-bundle."""
        if self.dry_run:
            LOG.info("No changes will be committed since this is a dry-run")
            return
        for path in fastq_paths:
            LOG.info(f"Adding path {path} to bundle {lims_sample_id} in housekeeper")
            self.housekeeper_api.add_and_include_file_to_latest_version(
                bundle_name=lims_sample_id, file=path, tags=HK_FASTQ_TAGS
            )

    def start_cases(self, cases: list[dict]) -> None:
        """Start cases that have not been analysed."""
        if self.dry_run:
            LOG.info("No cases will be started since this is a dry-run")
            return
        for case in cases:
            self.status_db.set_case_action(case_internal_id=case["internal_id"], action="analyze")
            LOG.info(f"Case {case['internal_id']} has been set to 'analyze'")

    def add_fastqs_to_housekeeper_and_start_cases(self) -> None:
        """
        Add and include available ticket fastq files to a Housekeeper bundle if they are not
        corrupted and start cases associated with the ticket.
        """
        available_sample_ids: list[str] = self.get_available_sample_ids()
        for sample_id in available_sample_ids:
            fastq_paths_to_add: list[Path] = self.get_fastq_paths_to_add(lims_sample_id=sample_id)
            if are_all_fastq_valid(fastq_paths=fastq_paths_to_add):
                self.add_and_include_files_to_bundles(
                    fastq_paths=fastq_paths_to_add,
                    lims_sample_id=sample_id,
                )
                self.start_cases(
                    cases=self.status_db.get_not_analysed_cases_by_sample_internal_id(
                        sample_internal_id=sample_id
                    )
                )
            else:
                LOG.warning(
                    f"Some files in {sample_id} did not match the given md5sum."
                    " Changes in housekeeper will not be committed and no cases will be started"
                )
