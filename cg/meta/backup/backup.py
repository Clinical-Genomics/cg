""" Module for retrieving flow cells from backup."""
import logging
import re
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import FileExtensions, FlowCellStatus
from cg.constants.backup import MAX_PROCESSING_FLOW_CELLS
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.indexes import ListIndexes
from cg.constants.pdc import PDCExitCodes
from cg.constants.process import RETURN_WARNING
from cg.constants.symbols import ASTERISK, NEW_LINE
from cg.exc import ChecksumFailedError, PdcNoFilesMatchingSearchError
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import EncryptionAPI, SpringEncryptionAPI
from cg.meta.tar.tar import TarAPI
from cg.models import CompressionData
from cg.store import Store
from cg.store.models import Flowcell
from cg.utils.time import get_elapsed_time, get_start_time

LOG = logging.getLogger(__name__)


class BackupAPI:
    """Class for retrieving FCs from backup."""

    def __init__(
        self,
        encryption_api: EncryptionAPI,
        encrypt_dir: Dict[str, str],
        status: Store,
        tar_api: TarAPI,
        pdc_api: PdcAPI,
        root_dir: Dict[str, str],
        dry_run: bool = False,
    ):
        self.encryption_api = encryption_api
        self.encrypt_dir = encrypt_dir
        self.status: Store = status
        self.tar_api: TarAPI = tar_api
        self.pdc: PdcAPI = pdc_api
        self.root_dir: dict = root_dir
        self.dry_run: bool = dry_run

    def check_processing(self) -> bool:
        """Check if the processing queue for flow cells is not full."""
        processing_flow_cells_count: int = len(
            self.status.get_flow_cells_by_statuses(flow_cell_statuses=[FlowCellStatus.PROCESSING])
        )
        LOG.debug(f"Processing flow cells: {processing_flow_cells_count}")
        return processing_flow_cells_count < MAX_PROCESSING_FLOW_CELLS

    def get_first_flow_cell(self) -> Optional[Flowcell]:
        """Get the first flow cell from the requested queue."""
        flow_cell: Optional[Flowcell] = self.status.get_flow_cells_by_statuses(
            flow_cell_statuses=[FlowCellStatus.REQUESTED]
        )
        return flow_cell[0] if flow_cell else None

    def fetch_flow_cell(self, flow_cell: Optional[Flowcell] = None) -> Optional[float]:
        """Start fetching a flow cell from backup if possible.

        1. The processing queue is not full.
        2. The requested queue is not emtpy.
        """
        if self.check_processing() is False:
            LOG.info("Processing queue is full")
            return None

        if not flow_cell:
            flow_cell: Optional[Flowcell] = self.get_first_flow_cell()

        if not flow_cell:
            LOG.info("No flow cells requested")
            return None

        flow_cell.status: FlowCellStatus = FlowCellStatus.PROCESSING
        if not self.dry_run:
            self.status.session.commit()
            LOG.info(f"{flow_cell.name}: retrieving from PDC")

        try:
            pdc_flow_cell_query: List[str] = self.query_pdc_for_flow_cell(flow_cell.name)

        except PdcNoFilesMatchingSearchError as error:
            LOG.error(f"PDC query failed: {error}")
            raise error

        archived_key: Path = self.get_archived_encryption_key_path(query=pdc_flow_cell_query)
        archived_flow_cell: Path = self.get_archived_flow_cell_path(query=pdc_flow_cell_query)

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
        run_dir: Path = Path(self.root_dir[flow_cell.sequencer_type])
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
            self.create_rta_complete(decrypted_flow_cell, run_dir)
            self.unlink_files(
                decrypted_flow_cell, encryption_key, retrieved_flow_cell, retrieved_key
            )
        except subprocess.CalledProcessError as error:
            LOG.error(f"Decryption failed: {error.stderr}")
            if not self.dry_run:
                flow_cell.status: str = FlowCellStatus.REQUESTED
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
    def create_rta_complete(decrypted_flow_cell: Path, run_dir: Path):
        """Create an RTAComplete.txt file in the flow cell run directory."""
        (
            run_dir / Path(decrypted_flow_cell.stem).stem / DemultiplexingDirsAndFiles.RTACOMPLETE
        ).touch()

    def extract_flow_cell(self, decrypted_flow_cell, run_dir):
        """Extract the flow cell tar archive."""
        extraction_command = self.tar_api.get_extract_file_command(
            input_file=decrypted_flow_cell, output_dir=run_dir
        )
        LOG.debug(f"Extract flow cell command: {extraction_command}")
        self.tar_api.run_tar_command(extraction_command)

    def decrypt_flow_cell(
        self, archived_flow_cell: Path, archived_key: Path, run_dir: Path
    ) -> Tuple[Path, Path, Path, Path]:
        """Decrypt the flow cell."""
        retrieved_key: Path = run_dir / archived_key.name
        encryption_key: Path = retrieved_key.with_suffix(FileExtensions.NO_EXTENSION)
        decryption_command: List[str] = self.encryption_api.get_asymmetric_decryption_command(
            input_file=retrieved_key, output_file=encryption_key
        )
        LOG.debug(f"Decrypt key command: {decryption_command}")
        self.encryption_api.run_gpg_command(decryption_command)
        retrieved_flow_cell: Path = run_dir / archived_flow_cell.name
        decrypted_flow_cell: Path = retrieved_flow_cell.with_suffix(FileExtensions.NO_EXTENSION)
        decryption_command: List[str] = self.encryption_api.get_symmetric_decryption_command(
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
        except subprocess.CalledProcessError as error:
            if error.returncode == RETURN_WARNING:
                LOG.warning(
                    f"WARNING for retrieval of encryption key of flow cell {flow_cell.name}, please check "
                    "dsmerror.log"
                )
            else:
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
        except subprocess.CalledProcessError as error:
            if error.returncode == RETURN_WARNING:
                LOG.warning(
                    f"WARNING for retrieval of flow cell {flow_cell.name}, please check dsmerror.log"
                )
                if not self.dry_run:
                    self._set_flow_cell_status_to_retrieved(flow_cell)
            else:
                LOG.error(f"{flow_cell.name}: run directory retrieval failed")
                if not self.dry_run:
                    flow_cell.status = FlowCellStatus.REQUESTED
                    self.status.session.commit()
                raise error

    def _set_flow_cell_status_to_retrieved(self, flow_cell: Flowcell):
        flow_cell.status = FlowCellStatus.RETRIEVED
        self.status.session.commit()
        LOG.info(f"Status for flow cell {flow_cell.name} set to {flow_cell.status}")

    def query_pdc_for_flow_cell(self, flow_cell_id) -> List[str]:
        """Query PDC for a given flow cell id."""
        search_patterns: List[str] = [
            dir + ASTERISK + flow_cell_id + ASTERISK for dir in self.encrypt_dir.values()
        ]

        for search_pattern in search_patterns:
            try:
                self.pdc.query_pdc(search_pattern=search_pattern)
                query: List[str] = self.pdc.process.stdout.split(NEW_LINE)
                continue
            except subprocess.CalledProcessError as error:
                if error.returncode != PDCExitCodes.NO_FILES_FOUND:
                    raise error
                LOG.info(
                    f"No archived files found for pdc query {search_patterns}, testing legacy directory"
                )

        if not query:
            raise PdcNoFilesMatchingSearchError(
                message=f"No archived files found for pdc queries {search_patterns}"
            )
        LOG.info(f"Found archived files for pdc queries {search_patterns}")
        return query

    def retrieve_archived_file(self, archived_file: Path, run_dir: Path) -> None:
        """Retrieve the archived file from PDC to a flow cell runs directory."""
        retrieved_file: Path = run_dir / archived_file.name
        LOG.debug(f"Retrieving file {archived_file} to {retrieved_file}")
        self.pdc.retrieve_file_from_pdc(
            file_path=str(archived_file), target_path=str(retrieved_file)
        )

    def get_archived_flow_cell_path(self, query: list) -> Path:
        """Get the path of the archived flow cell from a PDC query."""
        flow_cell_query: str = [
            row
            for row in query
            if FileExtensions.TAR in row
            and FileExtensions.GZIP in row
            and FileExtensions.GPG in row
        ][ListIndexes.FIRST.value]

        for dir in self.encrypt_dir.values():
            re_archived_flow_cell_path: re.Pattern = re.compile(dir + ".+?(?=\s)")
            arhived_flow_cell: Optional[re.Match] = re.search(
                re_archived_flow_cell_path, flow_cell_query
            )
            if arhived_flow_cell:
                archived_flow_cell_path: Path = Path(arhived_flow_cell.group())
                LOG.info(f"Flow cell found: {archived_flow_cell_path}")
                return archived_flow_cell_path

    def get_archived_encryption_key_path(self, query: list) -> Path:
        """Get the encryption key for the archived flow cell from a PDC query."""
        encryption_key_query: str = [
            row for row in query if FileExtensions.KEY in row and FileExtensions.GPG in row
        ][ListIndexes.FIRST.value]

        for dir in self.encrypt_dir.values():
            re_archived_encryption_key_path: re.Pattern = re.compile(dir + ".+?(?=\s)")
            archived_encryption_key: Optional[re.Match] = re.search(
                re_archived_encryption_key_path, encryption_key_query
            )
            if archived_encryption_key:
                archived_encryption_key_path: Path = Path(archived_encryption_key.group())
                LOG.info(f"Encryption key found: {archived_encryption_key_path}")
                return archived_encryption_key_path


class SpringBackupAPI:
    """Class for handling PDC backup and retrieval of spring compressed fastq files."""

    def __init__(
        self,
        encryption_api: SpringEncryptionAPI,
        pdc_api: PdcAPI,
        hk_api: HousekeeperAPI,
        dry_run: bool = False,
    ):
        self.encryption_api: SpringEncryptionAPI = encryption_api
        self.hk_api: HousekeeperAPI = hk_api
        self.pdc: PdcAPI = pdc_api
        self.dry_run = dry_run

    def encrypt_and_archive_spring_file(self, spring_file_path: Path) -> None:
        """Encrypts and archives a spring file and its decryption key."""
        LOG.debug(f"*** START BACKUP PROCESS OF SPRING FILE {spring_file_path} ***")
        if self.is_compression_ongoing(spring_file_path):
            LOG.info(
                f"Spring (de)compression ongoing, skipping archiving for spring file {spring_file_path}",
            )
            return
        self.encryption_api.cleanup(spring_file_path)
        if self.is_spring_file_archived(spring_file_path):
            LOG.info(
                "Spring file already archived! Spring file will be removed from disk, continuing "
                "to next spring file "
            )
            self.remove_archived_spring_file(spring_file_path)
            return
        try:
            self.encryption_api.spring_symmetric_encryption(spring_file_path)
            self.encryption_api.key_asymmetric_encryption(spring_file_path)
            self.encryption_api.compare_spring_file_checksums(spring_file_path)
            self.pdc.archive_file_to_pdc(
                file_path=str(self.encryption_api.encrypted_spring_file_path(spring_file_path)),
                dry_run=self.dry_run,
            )
            self.pdc.archive_file_to_pdc(
                file_path=str(self.encryption_api.encrypted_key_path(spring_file_path)),
                dry_run=self.dry_run,
            )
            self.mark_file_as_archived(spring_file_path)
            self.encryption_api.cleanup(spring_file_path)
            self.remove_archived_spring_file(spring_file_path)
            LOG.debug("*** ARCHIVING PROCESS COMPLETED SUCCESSFULLY ***")
        except subprocess.CalledProcessError as error:
            LOG.error(f"Encryption failed: {error.stderr}")
            LOG.debug("*** COMMAND PROCESS FAILED! ***")
            self.encryption_api.cleanup(spring_file_path)
        except ChecksumFailedError as error:
            LOG.error(error)
            self.encryption_api.cleanup(spring_file_path)
            LOG.debug("*** CHECKSUM PROCESS FAILED! ***")

    def retrieve_and_decrypt_spring_file(self, spring_file_path: Path) -> None:
        """Retrieves and decrypts a spring file and its decryption key."""
        LOG.info(f"*** START RETRIEVAL PROCESS OF SPRING FILE {spring_file_path} ***")
        try:
            self.pdc.retrieve_file_from_pdc(
                file_path=str(self.encryption_api.encrypted_spring_file_path(spring_file_path)),
            )
            self.pdc.retrieve_file_from_pdc(
                file_path=str(self.encryption_api.encrypted_key_path(spring_file_path)),
            )
            self.encryption_api.key_asymmetric_decryption(spring_file_path)
            self.encryption_api.spring_symmetric_decryption(
                spring_file_path, output_file=spring_file_path
            )
        except subprocess.CalledProcessError as error:
            LOG.error(f"Decryption failed: {error.stderr}")
            LOG.debug("*** RETRIEVAL PROCESS FAILED! ***")
        self.encryption_api.cleanup(spring_file_path)
        LOG.debug("*** RETRIEVAL PROCESS COMPLETED SUCCESSFULLY ***")

    def mark_file_as_archived(self, spring_file_path: Path) -> None:
        """Set the field 'to_archive' of the file in Housekeeper to mark that it has been
        archived to PDC."""
        if self.dry_run:
            LOG.info(f"Dry run, no changes made to {spring_file_path}")
            return
        hk_spring_file: File = self.hk_api.files(path=str(spring_file_path)).first()
        if hk_spring_file:
            LOG.info(f"Setting {spring_file_path} to archived in Housekeeper")
            self.hk_api.set_to_archive(file=hk_spring_file, value=True)
        else:
            LOG.warning(f"Could not find {spring_file_path} on disk")

    def remove_archived_spring_file(self, spring_file_path: Path) -> None:
        """Removes all files related to spring PDC archiving."""
        if not self.dry_run:
            LOG.info(f"Removing spring file {spring_file_path} from disk")
            spring_file_path.unlink()

    def is_to_be_retrieved_and_decrypted(self, spring_file_path: Path) -> bool:
        """Determines if a spring file is archived on PDC and needs to be retrieved and decrypted."""
        spring_file: File = self.hk_api.files(path=str(spring_file_path)).first()
        if spring_file and not spring_file_path.exists():
            return spring_file.to_archive
        return False

    def is_spring_file_archived(self, spring_file_path: Path) -> bool:
        """Checks if a spring file is marked as archived in Housekeeper."""
        spring_file: File = self.hk_api.files(path=str(spring_file_path)).first()
        if spring_file:
            return spring_file.to_archive
        return False

    @staticmethod
    def is_compression_ongoing(spring_file_path: Path) -> bool:
        """Determines if (de)compression of the spring file ongoing."""
        return CompressionData(spring_file_path).pending_exists()
