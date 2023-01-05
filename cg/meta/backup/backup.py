""" Module for retrieving FCs from backup """
import logging
import re
import subprocess
from pathlib import Path
from typing import Optional, Dict, List

from housekeeper.store import models as hk_models

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import FileExtensions, FlowCellStatus
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.indexes import ListIndexes
from cg.constants.process import RETURN_WARNING
from cg.constants.symbols import ASTERISK, NEW_LINE
from cg.exc import ChecksumFailedError, PdcNoFilesMatchingSearchError
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import EncryptionAPI, SpringEncryptionAPI
from cg.meta.tar.tar import TarAPI
from cg.models import CompressionData
from cg.store import Store, models
from cg.utils.time import get_elapsed_time, get_start_time

LOG = logging.getLogger(__name__)


class BackupAPI:
    """Class for retrieving FCs from backup"""

    def __init__(
        self,
        encryption_api: EncryptionAPI,
        encrypt_dirs: Dict[str, str],
        status: Store,
        tar_api: TarAPI,
        pdc_api: PdcAPI,
        root_dir: Dict[str, str],
        dry_run: bool = False,
    ):

        self.encryption_api = encryption_api
        self.encrypt_dirs = encrypt_dirs
        self.status: Store = status
        self.tar_api: TarAPI = tar_api
        self.pdc: PdcAPI = pdc_api
        self.root_dir: dict = root_dir
        self.dry_run: bool = dry_run

    def check_processing(self, max_processing_flow_cells: int = 1) -> bool:
        """Check if the processing queue for flow cells is not full."""
        processing_flow_cells = self.status.flowcells(status=FlowCellStatus.PROCESSING).count()
        LOG.debug("Processing flow cells: %s", processing_flow_cells)
        return processing_flow_cells < max_processing_flow_cells

    def get_first_flow_cell(self) -> Optional[models.Flowcell]:
        """Get the first flow cell from the requested queue"""
        flow_cell_obj: Optional[models.Flowcell] = self.status.flowcells(
            status=FlowCellStatus.REQUESTED
        ).first()
        return flow_cell_obj or None

    def fetch_flow_cell(self, flow_cell_obj: Optional[models.Flowcell] = None) -> Optional[float]:
        """Start fetching a flow cell from backup if possible.

        1. The processing queue is not full
        2. The requested queue is not emtpy
        """
        if self.check_processing() is False:
            LOG.info("Processing queue is full")
            return None

        if not flow_cell_obj:
            flow_cell_obj = self.get_first_flow_cell()

        if not flow_cell_obj:
            LOG.info("No flow cells requested")
            return None

        flow_cell_obj.status = FlowCellStatus.PROCESSING
        if not self.dry_run:
            self.status.commit()
            LOG.info("%s: retrieving from PDC", flow_cell_obj.name)

        try:
            pdc_flow_cell_query: List[str] = self.query_pdc_for_flow_cell(flow_cell_obj.name)

        except PdcNoFilesMatchingSearchError as error:
            LOG.error(f"PDC query failed: {error}")
            raise error

        archived_key: Path = self.get_archived_encryption_key_path(query=pdc_flow_cell_query)
        archived_flow_cell: Path = self.get_archived_flow_cell_path(query=pdc_flow_cell_query)

        if not self.dry_run:
            return self._process_flow_cell(flow_cell_obj, archived_key, archived_flow_cell)

    def _process_flow_cell(self, flow_cell_obj, archived_key, archived_flow_cell):
        start_time = get_start_time()
        run_dir: Path = Path(self.root_dir[flow_cell_obj.sequencer_type])
        self.retrieve_archived_key(archived_key, flow_cell_obj, run_dir)
        self.retrieve_archived_flow_cell(archived_flow_cell, flow_cell_obj, run_dir)

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
            LOG.error("Decryption failed: %s", error.stderr)
            if not self.dry_run:
                flow_cell_obj.status = FlowCellStatus.REQUESTED
                self.status.commit()
            raise error

        return get_elapsed_time(start_time=start_time)

    def unlink_files(
        self,
        decrypted_flow_cell: Path,
        encryption_key: Path,
        retrieved_flow_cell: Path,
        retrieved_key: Path,
    ):
        """Remove files after flow cell has been fetched from PDC"""
        if self.dry_run:
            return
        LOG.debug("Unlink files")
        message = "%s not found, skipping removal"
        try:
            retrieved_flow_cell.unlink()
        except FileNotFoundError:
            LOG.info(message, str(retrieved_flow_cell))
        try:
            decrypted_flow_cell.unlink()
        except FileNotFoundError:
            LOG.info(message, str(decrypted_flow_cell))
        try:
            retrieved_key.unlink()
        except FileNotFoundError:
            LOG.info(message, str(retrieved_key))
        try:
            encryption_key.unlink()
        except FileNotFoundError:
            LOG.info(message, str(encryption_key))

    @staticmethod
    def create_rta_complete(decrypted_flow_cell: Path, run_dir: Path):
        """Create an RTAComplete.txt file in the flow cell run directory"""
        (
            run_dir / Path(decrypted_flow_cell.stem).stem / DemultiplexingDirsAndFiles.RTACOMPLETE
        ).touch()

    def extract_flow_cell(self, decrypted_flow_cell, run_dir):
        """Extract the flow cell tar archive"""
        extraction_command = self.tar_api.get_extract_file_command(
            input_file=decrypted_flow_cell, output_dir=run_dir
        )
        LOG.debug(f"Extract flow cell command: {extraction_command}")
        self.tar_api.run_tar_command(extraction_command)

    def decrypt_flow_cell(self, archived_flow_cell, archived_key, run_dir):
        """Decrypt the flow cell"""
        retrieved_key = run_dir / archived_key.name
        encryption_key: Path = retrieved_key.with_suffix(FileExtensions.NO_EXTENSION)
        decryption_command = self.encryption_api.get_asymmetric_decryption_command(
            input_file=retrieved_key, output_file=encryption_key
        )
        LOG.debug(f"Decrypt key command: {decryption_command}")
        self.encryption_api.run_gpg_command(decryption_command)
        retrieved_flow_cell: Path = run_dir / archived_flow_cell.name
        decrypted_flow_cell: Path = retrieved_flow_cell.with_suffix(FileExtensions.NO_EXTENSION)
        decryption_command = self.encryption_api.get_symmetric_decryption_command(
            input_file=retrieved_flow_cell,
            output_file=decrypted_flow_cell,
            encryption_key=encryption_key,
        )
        LOG.debug(f"Decrypt flow cell command: {decryption_command}")
        self.encryption_api.run_gpg_command(decryption_command)
        return decrypted_flow_cell, encryption_key, retrieved_flow_cell, retrieved_key

    def retrieve_archived_key(
        self, archived_key: Path, flow_cell_obj: models.Flowcell, run_dir: Path
    ) -> None:
        """Attempt to retrieve an archived key"""
        try:
            self.retrieve_archived_file(
                archived_file=archived_key,
                run_dir=run_dir,
            )
        except subprocess.CalledProcessError as error:
            if error.returncode == RETURN_WARNING:
                LOG.warning(
                    "WARNING for retrieval of encryption key of flow cell %s, please check "
                    "dsmerror.log",
                    flow_cell_obj.name,
                )
            else:
                LOG.error("%s: key retrieval failed", flow_cell_obj.name)
                if not self.dry_run:
                    flow_cell_obj.status = FlowCellStatus.REQUESTED
                    self.status.commit()
                raise error

    def retrieve_archived_flow_cell(
        self, archived_flow_cell: Path, flow_cell_obj: models.Flowcell, run_dir: Path
    ):
        """Attempt to retrieve an archived flow cell"""
        try:
            self.retrieve_archived_file(
                archived_file=archived_flow_cell,
                run_dir=run_dir,
            )
            if not self.dry_run:
                self._set_flow_cell_status_to_retrieved(flow_cell_obj)
        except subprocess.CalledProcessError as error:
            if error.returncode == RETURN_WARNING:
                LOG.warning(
                    f"WARNING for retrieval of flow cell {flow_cell_obj.name}, please check dsmerror.log"
                )
                if not self.dry_run:
                    self._set_flow_cell_status_to_retrieved(flow_cell_obj)
            else:
                LOG.error(f"{flow_cell_obj.name}: run directory retrieval failed")
                if not self.dry_run:
                    flow_cell_obj.status = FlowCellStatus.REQUESTED
                    self.status.commit()
                raise error

    def _set_flow_cell_status_to_retrieved(self, flow_cell_obj: models.Flowcell):
        flow_cell_obj.status = FlowCellStatus.RETRIEVED
        self.status.commit()
        LOG.info(f"Status for flow cell {flow_cell_obj.name} set to {flow_cell_obj.status}")

    def query_pdc_for_flow_cell(self, flow_cell_id) -> List[str]:
        """Query PDC for a given flow cell id"""
        query: List[str] = []
        search_patterns: List[str] = [
            dir + ASTERISK + flow_cell_id + ASTERISK for dir in self.encrypt_dirs.values()
        ]

        for search_pattern in search_patterns:
            try:
                self.pdc.query_pdc(search_pattern=search_pattern)
                query.append(self.pdc.process.stdout.split(NEW_LINE))
            except subprocess.CalledProcessError as error:
                pdc_no_files_mathing_search_error: PdcNoFilesMatchingSearchError = (
                    PdcNoFilesMatchingSearchError(
                        message=f"No archived files found for pdc query {search_pattern}"
                    )
                )
                if error.returncode != pdc_no_files_mathing_search_error.exit_code:
                    raise error
                LOG.info(f"{pdc_no_files_mathing_search_error}")

        if not query:
            raise PdcNoFilesMatchingSearchError(
                message=f"No archived files found for pdc queries {search_patterns}"
            )
        LOG.info(f"Found archived files for pdc queries {search_patterns}")
        return query

    def retrieve_archived_file(self, archived_file: Path, run_dir: Path) -> None:
        """Retrieve the archived file from PDC to a flow cell runs directory"""
        retrieved_file: Path = run_dir / archived_file.name
        LOG.debug(f"Retrieving file {archived_file} to {retrieved_file}")
        self.pdc.retrieve_file_from_pdc(
            file_path=str(archived_file), target_path=str(retrieved_file)
        )

    def get_archived_flow_cell_path(self, query: list) -> Path:
        """Get the path of the archived flow cell from a PDC query"""
        flow_cell_query: str = [
            row
            for row in query
            if FileExtensions.TAR in row
            and FileExtensions.GZIP in row
            and FileExtensions.GPG in row
        ][ListIndexes.FIRST.value]

        for dir in self.encrypt_dirs.values():
            re_archived_flow_cell_path: re.Pattern = re.compile(dir + ".+?(?=\s)")
            archived_flow_cell_path = Path(
                re.search(re_archived_flow_cell_path, flow_cell_query).group()
            )
            if archived_flow_cell_path:
                LOG.info("Flow cell found: %s", str(archived_flow_cell_path))
                return archived_flow_cell_path

    def get_archived_encryption_key_path(self, query: list) -> Path:
        """Get the encryption key for the archived flow cell from a PDC query"""
        LOG.info(f"{query}")
        encryption_key_query: str = [
            row for row in query if FileExtensions.KEY in row and FileExtensions.GPG in row
        ][ListIndexes.FIRST.value]

        for dir in self.encrypt_dirs.values():
            re_archived_encryption_key_path: re.Pattern = re.compile(dir + ".+?(?=\s)")
            archived_encryption_key_path = Path(
                re.search(re_archived_encryption_key_path, encryption_key_query).group()
            )
            if archived_encryption_key_path:
                LOG.info("Encryption key found: %s", str(archived_encryption_key_path))
                return archived_encryption_key_path


class SpringBackupAPI:
    """Class for handling PDC backup and retrieval of spring compressed fastq files"""

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
        """Encrypts and archives a spring file and its decryption key"""
        LOG.debug(f"*** START BACKUP PROCESS OF SPRING FILE %s ***", spring_file_path)
        if self.is_compression_ongoing(spring_file_path):
            LOG.info(
                "Spring (de)compression ongoing, skipping archiving for spring file %s",
                spring_file_path,
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
            LOG.debug(f"*** ARCHIVING PROCESS COMPLETED SUCCESSFULLY ***")
        except subprocess.CalledProcessError as error:
            LOG.error("Encryption failed: %s", error.stderr)
            LOG.debug(f"*** COMMAND PROCESS FAILED! ***")
            self.encryption_api.cleanup(spring_file_path)
        except ChecksumFailedError as error:
            LOG.error(error)
            self.encryption_api.cleanup(spring_file_path)
            LOG.debug(f"*** CHECKSUM PROCESS FAILED! ***")

    def retrieve_and_decrypt_spring_file(self, spring_file_path: Path) -> None:
        """Retrieves and decrypts a spring file and its decryption key"""
        LOG.info(f"*** START RETRIEVAL PROCESS OF SPRING FILE %s ***", spring_file_path)
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
            LOG.error("Decryption failed: %s", error.stderr)
            LOG.debug(f"*** RETRIEVAL PROCESS FAILED! ***")
        self.encryption_api.cleanup(spring_file_path)
        LOG.debug(f"*** RETRIEVAL PROCESS COMPLETED SUCCESSFULLY ***")

    def mark_file_as_archived(self, spring_file_path: Path) -> None:
        """Set the field 'to_archive' of the file in Housekeeper to mark that it has been
        archived to PDC"""
        if self.dry_run:
            LOG.info("Dry run, no changes made to %s", spring_file_path)
            return
        hk_spring_file: hk_models.File = self.hk_api.files(path=str(spring_file_path)).first()
        LOG.info("Setting %s to archived in Housekeeper", spring_file_path)
        self.hk_api.set_to_archive(file=hk_spring_file, value=True)

    def is_to_be_retrieved_and_decrypted(self, spring_file_path: Path) -> bool:
        """Determines if a spring file is archived on PDC and needs to be retrieved and decrypted"""
        return (
            self.hk_api.files(path=str(spring_file_path)).first().to_archive
            and not spring_file_path.exists()
        )

    def remove_archived_spring_file(self, spring_file_path: Path) -> None:
        """Removes all files related to spring PDC archiving"""
        if not self.dry_run:
            LOG.info("Removing spring file %s from disk", str(spring_file_path))
            spring_file_path.unlink()

    def is_spring_file_archived(self, spring_file_path: Path) -> bool:
        """Checks if a spring file is marked as archived in Housekeeper"""
        return self.hk_api.files(path=str(spring_file_path)).first().to_archive

    @staticmethod
    def is_compression_ongoing(spring_file_path: Path) -> bool:
        """Determines if (de)compression of the spring file ongoing"""
        return CompressionData(spring_file_path).pending_exists()
