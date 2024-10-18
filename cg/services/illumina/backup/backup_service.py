import subprocess
from pathlib import Path

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants import FileExtensions, SequencingRunDataAvailability
from cg.constants.backup import MAX_PROCESSING_ILLUMINA_RUNS
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.exc import (
    DsmcAlreadyRunningError,
    IlluminaRunAlreadyBackedUpError,
    IlluminaRunEncryptionError,
    PdcError,
    PdcNoFilesMatchingSearchError,
)
from cg.meta.backup.backup import LOG
from cg.meta.encryption.encryption import EncryptionAPI
from cg.meta.tar.tar import TarAPI
from cg.models.cg_config import PDCArchivingDirectory
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.backup.encrypt_service import IlluminaRunEncryptionService
from cg.services.illumina.backup.utils import (
    get_latest_archived_encryption_key_path,
    get_latest_archived_sequencing_run_path,
)
from cg.services.pdc_service.pdc_service import PdcService
from cg.store.models import IlluminaSequencingRun
from cg.store.store import Store
from cg.utils.time import get_elapsed_time, get_start_time


class IlluminaBackupService:
    """Class for retrieving FCs from backup."""

    def __init__(
        self,
        encryption_api: EncryptionAPI,
        pdc_archiving_directory: PDCArchivingDirectory,
        status_db: Store,
        tar_api: TarAPI,
        pdc_service: PdcService,
        sequencing_runs_dir: str,
        dry_run: bool = False,
    ):
        self.encryption_api = encryption_api
        self.pdc_archiving_directory: PDCArchivingDirectory = pdc_archiving_directory
        self.status_db: Store = status_db
        self.tar_api: TarAPI = tar_api
        self.pdc: PdcService = pdc_service
        self.sequencing_runs_dir: str = sequencing_runs_dir
        self.dry_run: bool = dry_run

    def has_processing_queue_capacity(self) -> bool:
        """Check if the processing queue for illumina runs is not full."""
        proccessing_runs_count: int = len(
            self.status_db.get_illumina_sequencing_runs_by_data_availability(
                data_availability=[SequencingRunDataAvailability.PROCESSING]
            )
        )
        LOG.debug(f"Processing illumina runs: {proccessing_runs_count}")
        return proccessing_runs_count < MAX_PROCESSING_ILLUMINA_RUNS

    def get_first_run(self) -> IlluminaSequencingRun | None:
        """Get the sequencing run from the requested queue."""
        sequencing_run: list[IlluminaSequencingRun] | None = (
            self.status_db.get_illumina_sequencing_runs_by_data_availability(
                data_availability=[SequencingRunDataAvailability.REQUESTED]
            )
        )
        return sequencing_run[0] if sequencing_run else None

    def fetch_sequencing_run(
        self, sequencing_run: IlluminaSequencingRun | None = None
    ) -> float | None:
        """Start fetching a sequencing run from backup if possible.
        A run can only be fetched when:
            1. The processing queue is not full.
            2. The requested queue is not emtpy.
        """
        if not self.has_processing_queue_capacity():
            LOG.info("Processing queue is full")
            return None

        if not sequencing_run:
            sequencing_run: IlluminaSequencingRun | None = self.get_first_run()

        if not sequencing_run:
            LOG.info("No sequencing run requested")
            return None

        if not self.dry_run:
            self.status_db.update_illumina_sequencing_run_data_availability(
                sequencing_run=sequencing_run,
                data_availability=SequencingRunDataAvailability.PROCESSING,
            )
            LOG.info(f"{sequencing_run.device.internal_id}: retrieving from PDC")

        dsmc_output: list[str] = self.query_pdc_for_sequencing_run(
            sequencing_run.device.internal_id
        )

        archived_key: Path = get_latest_archived_encryption_key_path(dsmc_output=dsmc_output)
        archived_run: Path = get_latest_archived_sequencing_run_path(dsmc_output=dsmc_output)

        if not self.dry_run:
            return self._process_run(
                sequencing_run=sequencing_run,
                archived_key=archived_key,
                archived_run=archived_run,
            )

    def _process_run(
        self, sequencing_run: IlluminaSequencingRun, archived_key: Path, archived_run: Path
    ) -> float:
        """Process a flow cell from backup. Return elapsed time."""
        start_time: float = get_start_time()
        run_dir = Path(self.sequencing_runs_dir)
        sequencing_run_output_dir = Path(run_dir, archived_run.name.split(".")[0])
        self.retrieve_archived_key(
            archived_key=archived_key, sequencing_run=sequencing_run, run_dir=run_dir
        )
        self.retrieve_archived_sequencing_run(
            archived_run=archived_run, sequencing_run=sequencing_run, run_dir=run_dir
        )

        try:
            (
                decrypted_run,
                encryption_key,
                retrieved_run,
                retrieved_key,
            ) = self.decrypt_sequencing_run(archived_run, archived_key, run_dir)

            self.extract_sequencing_run(decrypted_run, run_dir)
            self.create_rta_complete(sequencing_run_output_dir)
            self.create_copy_complete(sequencing_run_output_dir)
            self.unlink_files(decrypted_run, encryption_key, retrieved_run, retrieved_key)
        except subprocess.CalledProcessError as error:
            LOG.error(f"Decryption failed: {error.stderr}")
            if not self.dry_run:
                self.status_db.update_illumina_sequencing_run_data_availability(
                    sequencing_run=sequencing_run,
                    data_availability=SequencingRunDataAvailability.REQUESTED,
                )
            raise error

        return get_elapsed_time(start_time=start_time)

    def unlink_files(
        self,
        decrypted_run: Path,
        encryption_key: Path,
        retrieved_run: Path,
        retrieved_key: Path,
    ):
        """Remove files after the sequencing run has been fetched from PDC."""
        if self.dry_run:
            return
        LOG.debug("Unlink files")
        message = f"{retrieved_run} not found, skipping removal"
        try:
            retrieved_run.unlink()
        except FileNotFoundError:
            LOG.info(message)
        try:
            decrypted_run.unlink()
        except FileNotFoundError:
            LOG.info(message)
        try:
            retrieved_key.unlink()
        except FileNotFoundError:
            LOG.info(message)
        try:
            encryption_key.unlink()
        except FileNotFoundError:
            LOG.info(message)

    @staticmethod
    def create_rta_complete(flow_cell_directory: Path):
        """Create an RTAComplete.txt file in the flow cell run directory."""
        Path(flow_cell_directory, DemultiplexingDirsAndFiles.RTACOMPLETE).touch()

    @staticmethod
    def create_copy_complete(flow_cell_directory: Path):
        """Create a CopyComplete.txt file in the flow cell run directory."""
        Path(flow_cell_directory, DemultiplexingDirsAndFiles.COPY_COMPLETE).touch()

    def extract_sequencing_run(self, decrypted_run, run_dir):
        """Extract the sequencing run tar archive."""
        extraction_command = self.tar_api.get_extract_file_command(
            input_file=decrypted_run, output_dir=run_dir
        )
        LOG.debug(f"Extract sequencing run command: {extraction_command}")
        self.tar_api.run_tar_command(extraction_command)

    def decrypt_sequencing_run(
        self, archived_run: Path, archived_key: Path, run_dir: Path
    ) -> tuple[Path, Path, Path, Path]:
        """Decrypt the sequencing run."""
        retrieved_key: Path = run_dir / archived_key.name
        encryption_key: Path = retrieved_key.with_suffix(FileExtensions.NO_EXTENSION)
        decryption_command: list[str] = self.encryption_api.get_asymmetric_decryption_command(
            input_file=retrieved_key, output_file=encryption_key
        )
        LOG.debug(f"Decrypt key command: {decryption_command}")
        self.encryption_api.run_gpg_command(decryption_command)
        retrieved_run: Path = run_dir / archived_run.name
        decrypted_run: Path = retrieved_run.with_suffix(FileExtensions.NO_EXTENSION)
        decryption_command: list[str] = self.encryption_api.get_symmetric_decryption_command(
            input_file=retrieved_run,
            output_file=decrypted_run,
            encryption_key=encryption_key,
        )
        LOG.debug(f"Decrypt sequencing run command: {decryption_command}")
        self.encryption_api.run_gpg_command(decryption_command)
        return decrypted_run, encryption_key, retrieved_run, retrieved_key

    def retrieve_archived_key(
        self, archived_key: Path, sequencing_run: IlluminaSequencingRun, run_dir: Path
    ) -> None:
        """Attempt to retrieve an archived key."""
        try:
            self.retrieve_archived_file(
                archived_file=archived_key,
                run_dir=run_dir,
            )
        except PdcError as error:
            LOG.error(f"{sequencing_run.device.internal_id}: key retrieval failed")
            if not self.dry_run:
                self.status_db.update_illumina_sequencing_run_data_availability(
                    sequencing_run=sequencing_run,
                    data_availability=SequencingRunDataAvailability.REQUESTED,
                )
            raise error

    def retrieve_archived_sequencing_run(
        self, archived_run: Path, sequencing_run: IlluminaSequencingRun, run_dir: Path
    ):
        """Attempt to retrieve an archived sequencing run."""
        try:
            self.retrieve_archived_file(
                archived_file=archived_run,
                run_dir=run_dir,
            )
            if not self.dry_run:
                self.status_db.update_illumina_sequencing_run_data_availability(
                    sequencing_run=sequencing_run,
                    data_availability=SequencingRunDataAvailability.RETRIEVED,
                )
        except PdcError as error:
            LOG.error(f"{sequencing_run.device.internal_id}: run directory retrieval failed")
            if not self.dry_run:
                self.status_db.update_illumina_sequencing_run_data_availability(
                    sequencing_run=sequencing_run,
                    data_availability=SequencingRunDataAvailability.REQUESTED,
                )
            raise error

    def query_pdc_for_sequencing_run(self, flow_cell_id: str) -> list[str]:
        """Query PDC for a given flow cell id.
        Raise:
            PdcNoFilesMatchingSearchError if no files are found.
        """
        for _, encryption_directory in self.pdc_archiving_directory:
            search_pattern = f"{encryption_directory}*{flow_cell_id}*{FileExtensions.GPG}"
            self.pdc.query_pdc(search_pattern)
            if self.pdc.was_file_found(self.pdc.process.stderr):
                LOG.info(f"Found archived files for PDC query: {search_pattern}")
                return self.pdc.process.stdout.split("\n")
            LOG.debug(f"No archived files found for PDC query: {search_pattern}")

        raise PdcNoFilesMatchingSearchError(
            message=f"No flow cell files found at PDC for {flow_cell_id}"
        )

    def retrieve_archived_file(self, archived_file: Path, run_dir: Path) -> None:
        """Retrieve the archived file from PDC to a sequencing runs directory."""
        retrieved_file = Path(run_dir, archived_file.name)
        LOG.debug(f"Retrieving file {archived_file} to {retrieved_file}")
        self.pdc.retrieve_file_from_pdc(
            file_path=str(archived_file), target_path=str(retrieved_file)
        )

    def validate_is_run_backup_possible(
        self,
        sequencing_run: IlluminaSequencingRun,
        illumina_run_encryption_service: IlluminaRunEncryptionService,
    ) -> None:
        """Check if back-up of sequencing run is possible.
        Raises:
            DsmcAlreadyRunningError if there is already a Dsmc process ongoing.
            IlluminaRunAlreadyBackupError if sequencing run is already backed up.
            IlluminaRunEncryptionError if encryption is not complete.
        """
        if self.pdc.validate_is_dsmc_running():
            raise DsmcAlreadyRunningError("Too many Dsmc processes are already running")
        if sequencing_run and sequencing_run.has_backup:
            raise IlluminaRunAlreadyBackedUpError(
                f"Sequencing run for flow cell: {sequencing_run.device.internal_id} is already backed-up"
            )
        if not illumina_run_encryption_service.complete_file_path.exists():
            raise IlluminaRunEncryptionError(
                f"Sequencing run for flow cell: {illumina_run_encryption_service.run_dir_data.id} encryption process is not complete"
            )
        LOG.debug("Sequencing run can be backed up")

    def backup_run(
        self, files_to_archive: list[Path], store: Store, sequencing_run: IlluminaSequencingRun
    ) -> None:
        """Back-up sequecing run files."""
        for encrypted_file in files_to_archive:
            if not self.dry_run:
                self.pdc.archive_file_to_pdc(file_path=encrypted_file.as_posix())
        if not self.dry_run:
            store.update_illumina_sequencing_run_has_backup(
                sequencing_run=sequencing_run, has_backup=True
            )
            LOG.info(
                f"Illumina run for flow cell: {sequencing_run.device.internal_id} has been backed up"
            )

    def start_run_backup(
        self,
        sequencing_run: IlluminaSequencingRun,
        run_dir_data: IlluminaRunDirectoryData,
        status_db: Store,
        binary_path: str,
        encryption_dir: Path,
        pigz_binary_path,
        sbatch_parameter,
    ) -> None:
        """Check if back-up of flow cell is possible and if so starts it."""
        illumina_run_encryption_service = IlluminaRunEncryptionService(
            binary_path=binary_path,
            dry_run=self.dry_run,
            encryption_dir=encryption_dir,
            run_dir_data=run_dir_data,
            pigz_binary_path=pigz_binary_path,
            slurm_api=SlurmAPI(),
            sbatch_parameter=sbatch_parameter,
            tar_api=self.tar_api,
        )
        self.validate_is_run_backup_possible(
            sequencing_run=sequencing_run,
            illumina_run_encryption_service=illumina_run_encryption_service,
        )
        self.backup_run(
            files_to_archive=[
                illumina_run_encryption_service.final_passphrase_file_path,
                illumina_run_encryption_service.encrypted_gpg_file_path,
            ],
            store=status_db,
            sequencing_run=sequencing_run,
        )
