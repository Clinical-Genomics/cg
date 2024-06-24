import subprocess
from pathlib import Path

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants import FlowCellStatus, FileExtensions
from cg.constants.backup import MAX_PROCESSING_FLOW_CELLS
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.exc import (
    PdcError,
    PdcNoFilesMatchingSearchError,
    DsmcAlreadyRunningError,
    FlowCellAlreadyBackedUpError,
    IlluminaRunEncryptionError,
)
from cg.meta.backup.backup import LOG
from cg.meta.encryption.encryption import EncryptionAPI
from cg.services.illumina_services.backup_services.encrypt_service import (
    IlluminaRunEncryptionService,
)
from cg.meta.tar.tar import TarAPI
from cg.models.cg_config import PDCArchivingDirectory
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.pdc_service.pdc_service import PdcService
from cg.store.models import Flowcell
from cg.store.store import Store
from cg.utils.time import get_start_time, get_elapsed_time


class IlluminaBackupService:
    """Class for retrieving FCs from backup."""

    def __init__(
        self,
        encryption_api: EncryptionAPI,
        pdc_archiving_directory: PDCArchivingDirectory,
        status: Store,
        tar_api: TarAPI,
        pdc_service: PdcService,
        flow_cells_dir: str,
        dry_run: bool = False,
    ):
        self.encryption_api = encryption_api
        self.pdc_archiving_directory: PDCArchivingDirectory = pdc_archiving_directory
        self.status: Store = status
        self.tar_api: TarAPI = tar_api
        self.pdc: PdcService = pdc_service
        self.flow_cells_dir: str = flow_cells_dir
        self.dry_run: bool = dry_run

    def check_processing(self) -> bool:
        """Check if the processing queue for flow cells is not full."""
        processing_flow_cells_count: int = len(
            self.status.get_flow_cells_by_statuses(flow_cell_statuses=[FlowCellStatus.PROCESSING])
        )
        LOG.debug(f"Processing flow cells: {processing_flow_cells_count}")
        return processing_flow_cells_count < MAX_PROCESSING_FLOW_CELLS

    def get_first_flow_cell(self) -> Flowcell | None:
        """Get the first flow cell from the requested queue."""
        flow_cell: Flowcell | None = self.status.get_flow_cells_by_statuses(
            flow_cell_statuses=[FlowCellStatus.REQUESTED]
        )
        return flow_cell[0] if flow_cell else None

    def fetch_flow_cell(self, flow_cell: Flowcell | None = None) -> float | None:
        """Start fetching a flow cell from backup if possible.

        1. The processing queue is not full.
        2. The requested queue is not emtpy.
        """
        if self.check_processing() is False:
            LOG.info("Processing queue is full")
            return None

        if not flow_cell:
            flow_cell: Flowcell | None = self.get_first_flow_cell()

        if not flow_cell:
            LOG.info("No flow cells requested")
            return None

        flow_cell.status = FlowCellStatus.PROCESSING
        if not self.dry_run:
            self.status.session.commit()
            LOG.info(f"{flow_cell.name}: retrieving from PDC")

        dsmc_output: list[str] = self.query_pdc_for_flow_cell(flow_cell.name)

        archived_key: Path = self.get_archived_encryption_key_path(dsmc_output=dsmc_output)
        archived_flow_cell: Path = self.get_archived_flow_cell_path(dsmc_output=dsmc_output)

        if not self.dry_run:
            return self._process_flow_cell(
                flow_cell=flow_cell,
                archived_key=archived_key,
                archived_flow_cell=archived_flow_cell,
            )

    def _process_flow_cell(
        self, flow_cell: Flowcell, archived_key: Path, archived_flow_cell: Path
    ) -> float:
        """Process a flow cell from backup. Return elapsed time."""
        start_time: float = get_start_time()
        run_dir: Path = Path(self.flow_cells_dir)
        flow_cell_output_directory: Path = Path(run_dir, archived_flow_cell.name.split(".")[0])
        self.retrieve_archived_key(archived_key=archived_key, flow_cell=flow_cell, run_dir=run_dir)
        self.retrieve_archived_flow_cell(
            archived_flow_cell=archived_flow_cell, flow_cell=flow_cell, run_dir=run_dir
        )

        try:
            (
                decrypted_flow_cell,
                encryption_key,
                retrieved_flow_cell,
                retrieved_key,
            ) = self.decrypt_flow_cell(archived_flow_cell, archived_key, run_dir)

            self.extract_flow_cell(decrypted_flow_cell, run_dir)
            self.create_rta_complete(flow_cell_output_directory)
            self.create_copy_complete(flow_cell_output_directory)
            self.unlink_files(
                decrypted_flow_cell, encryption_key, retrieved_flow_cell, retrieved_key
            )
        except subprocess.CalledProcessError as error:
            LOG.error(f"Decryption failed: {error.stderr}")
            if not self.dry_run:
                flow_cell.status = FlowCellStatus.REQUESTED
                self.status.session.commit()
            raise error

        return get_elapsed_time(start_time=start_time)

    def unlink_files(
        self,
        decrypted_flow_cell: Path,
        encryption_key: Path,
        retrieved_flow_cell: Path,
        retrieved_key: Path,
    ):
        """Remove files after flow cell has been fetched from PDC."""
        if self.dry_run:
            return
        LOG.debug("Unlink files")
        message = f"{retrieved_flow_cell} not found, skipping removal"
        try:
            retrieved_flow_cell.unlink()
        except FileNotFoundError:
            LOG.info(message)
        try:
            decrypted_flow_cell.unlink()
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

    def extract_flow_cell(self, decrypted_flow_cell, run_dir):
        """Extract the flow cell tar archive."""
        extraction_command = self.tar_api.get_extract_file_command(
            input_file=decrypted_flow_cell, output_dir=run_dir
        )
        LOG.debug(f"Extract flow cell command: {extraction_command}")
        self.tar_api.run_tar_command(extraction_command)

    def decrypt_flow_cell(
        self, archived_flow_cell: Path, archived_key: Path, run_dir: Path
    ) -> tuple[Path, Path, Path, Path]:
        """Decrypt the flow cell."""
        retrieved_key: Path = run_dir / archived_key.name
        encryption_key: Path = retrieved_key.with_suffix(FileExtensions.NO_EXTENSION)
        decryption_command: list[str] = self.encryption_api.get_asymmetric_decryption_command(
            input_file=retrieved_key, output_file=encryption_key
        )
        LOG.debug(f"Decrypt key command: {decryption_command}")
        self.encryption_api.run_gpg_command(decryption_command)
        retrieved_flow_cell: Path = run_dir / archived_flow_cell.name
        decrypted_flow_cell: Path = retrieved_flow_cell.with_suffix(FileExtensions.NO_EXTENSION)
        decryption_command: list[str] = self.encryption_api.get_symmetric_decryption_command(
            input_file=retrieved_flow_cell,
            output_file=decrypted_flow_cell,
            encryption_key=encryption_key,
        )
        LOG.debug(f"Decrypt flow cell command: {decryption_command}")
        self.encryption_api.run_gpg_command(decryption_command)
        return decrypted_flow_cell, encryption_key, retrieved_flow_cell, retrieved_key

    def retrieve_archived_key(self, archived_key: Path, flow_cell: Flowcell, run_dir: Path) -> None:
        """Attempt to retrieve an archived key."""
        try:
            self.retrieve_archived_file(
                archived_file=archived_key,
                run_dir=run_dir,
            )
        except PdcError as error:
            LOG.error(f"{flow_cell.name}: key retrieval failed")
            if not self.dry_run:
                flow_cell.status = FlowCellStatus.REQUESTED
                self.status.session.commit()
            raise error

    def retrieve_archived_flow_cell(
        self, archived_flow_cell: Path, flow_cell: Flowcell, run_dir: Path
    ):
        """Attempt to retrieve an archived flow cell."""
        try:
            self.retrieve_archived_file(
                archived_file=archived_flow_cell,
                run_dir=run_dir,
            )
            if not self.dry_run:
                self._set_flow_cell_status_to_retrieved(flow_cell)
        except PdcError as error:
            LOG.error(f"{flow_cell.name}: run directory retrieval failed")
            if not self.dry_run:
                flow_cell.status = FlowCellStatus.REQUESTED
                self.status.session.commit()
            raise error

    def _set_flow_cell_status_to_retrieved(self, flow_cell: Flowcell):
        flow_cell.status = FlowCellStatus.RETRIEVED
        self.status.session.commit()
        LOG.info(f"Status for flow cell {flow_cell.name} set to {flow_cell.status}")

    def query_pdc_for_flow_cell(self, flow_cell_id: str) -> list[str]:
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
        """Retrieve the archived file from PDC to a flow cell runs directory."""
        retrieved_file = Path(run_dir, archived_file.name)
        LOG.debug(f"Retrieving file {archived_file} to {retrieved_file}")
        self.pdc.retrieve_file_from_pdc(
            file_path=str(archived_file), target_path=str(retrieved_file)
        )

    @classmethod
    def get_archived_flow_cell_path(cls, dsmc_output: list[str]) -> Path | None:
        """Get the path of the archived flow cell from a PDC query."""
        flow_cell_line: str = [
            row
            for row in dsmc_output
            if FileExtensions.TAR in row
            and FileExtensions.GZIP in row
            and FileExtensions.GPG in row
        ][0]

        archived_flow_cell = Path(flow_cell_line.split()[4])
        if archived_flow_cell:
            LOG.info(f"Flow cell found: {archived_flow_cell}")
            return archived_flow_cell

    @classmethod
    def get_archived_encryption_key_path(cls, dsmc_output: list[str]) -> Path | None:
        """Get the encryption key for the archived flow cell from a PDC query."""
        encryption_key_line: str = [
            row
            for row in dsmc_output
            if FileExtensions.KEY in row
            and FileExtensions.GPG in row
            and FileExtensions.GZIP not in row
        ][0]

        archived_encryption_key = Path(encryption_key_line.split()[4])
        if archived_encryption_key:
            LOG.info(f"Encryption key found: {archived_encryption_key}")
            return archived_encryption_key

    def validate_is_flow_cell_backup_possible(
        self, db_flow_cell: Flowcell, illumina_run_encryption_service: IlluminaRunEncryptionService
    ) -> None:
        """Check if back-up of flow cell is possible.
        Raises:
            DsmcAlreadyRunningError if there is already a Dsmc process ongoing.
            FlowCellAlreadyBackupError if flow cell is already backed up.
            FlowCellEncryptionError if encryption is not complete.
        """
        if self.pdc.validate_is_dsmc_running():
            raise DsmcAlreadyRunningError("Too many Dsmc processes are already running")
        if db_flow_cell and db_flow_cell.has_backup:
            raise FlowCellAlreadyBackedUpError(
                f"Flow cell: {db_flow_cell.name} is already backed-up"
            )
        if not illumina_run_encryption_service.complete_file_path.exists():
            raise IlluminaRunEncryptionError(
                f"Flow cell: {illumina_run_encryption_service.run_dir_data.id} encryption process is not complete"
            )
        LOG.debug("Flow cell can be backed up")

    def backup_flow_cell(
        self, files_to_archive: list[Path], store: Store, db_flow_cell: Flowcell
    ) -> None:
        """Back-up flow cell files."""
        for encrypted_file in files_to_archive:
            if not self.dry_run:
                self.pdc.archive_file_to_pdc(file_path=encrypted_file.as_posix())
        if not self.dry_run:
            store.update_flow_cell_has_backup(flow_cell=db_flow_cell, has_backup=True)
            LOG.info(f"Flow cell: {db_flow_cell.name} has been backed up")

    def start_flow_cell_backup(
        self,
        db_flow_cell: Flowcell,
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
        self.validate_is_flow_cell_backup_possible(
            db_flow_cell=db_flow_cell,
            illumina_run_encryption_service=illumina_run_encryption_service,
        )
        self.backup_flow_cell(
            files_to_archive=[
                illumina_run_encryption_service.final_passphrase_file_path,
                illumina_run_encryption_service.encrypted_gpg_file_path,
            ],
            store=status_db,
            db_flow_cell=db_flow_cell,
        )
