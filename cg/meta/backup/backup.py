""" Module for retrieving FCs from backup """
import logging
import subprocess
from pathlib import Path
from typing import Optional

from housekeeper.store import models as hk_models

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import FileExtensions, FlowCellStatus
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.encryption import EncryptionDirsAndFiles
from cg.constants.indexes import ListIndexes
from cg.constants.process import RETURN_WARNING
from cg.constants.symbols import ASTERISK, NEW_LINE, SPACE
from cg.exc import ChecksumFailedError
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import EncryptionAPI, SpringEncryptionAPI
from cg.meta.tar.tar import TarAPI
from cg.models import CompressionData
from cg.store import Store, models
from cg.utils.time import get_elapsed_time, get_start_time

LOG = logging.getLogger(__name__)


class BackupApi:
    """Class for retrieving FCs from backup"""

    def __init__(
        self,
        encryption_api: EncryptionAPI,
        status: Store,
        tar_api: TarAPI,
        pdc_api: PdcAPI,
        root_dir: dict,
    ):

        self.encryption_api = encryption_api
        self.status: Store = status
        self.tar_api: TarAPI = tar_api
        self.pdc: PdcAPI = pdc_api
        self.root_dir: dict = root_dir

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
        if not flow_cell_obj:
            return None
        return flow_cell_obj

    def fetch_flow_cell(
        self, flow_cell_obj: Optional[models.Flowcell] = None, dry_run: bool = False
    ) -> Optional[float]:
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
        if not dry_run:
            self.status.commit()
            LOG.info("%s: retrieving from PDC", flow_cell_obj.name)

        try:
            pdc_flow_cell_query: list = self.query_pdc_for_flow_cell(flow_cell_obj.name)
        except subprocess.CalledProcessError as error:
            LOG.error("PDC query failed: %s", error.stderr)
            raise error

        root_dir: Path = Path(self.root_dir[flow_cell_obj.sequencer_type])
        LOG.debug(f"Root dir: {root_dir}")
        archived_flow_cell: Path = self.get_archived_flow_cell(pdc_flow_cell_query)
        LOG.debug(f"Archived flow cell: {archived_flow_cell}")
        retrieved_flow_cell: Path = root_dir / archived_flow_cell.name
        LOG.debug(f"Retrieved flow cell: {retrieved_flow_cell}")
        decrypted_flow_cell: Path = retrieved_flow_cell.with_suffix(FileExtensions.NO_EXTENSION)
        LOG.debug(f"Decrypted flow cell: {decrypted_flow_cell}")
        encrypted_key: Path = self.get_archived_encryption_key(pdc_flow_cell_query)
        LOG.debug(f"Encrypted key: {encrypted_key}")
        retrieved_key: Path = root_dir / encrypted_key.name
        encryption_key: Path = retrieved_key.with_suffix(FileExtensions.NO_EXTENSION)
        LOG.debug(f"Encryption key: {encryption_key}")
        extraction_target_dir = root_dir / Path(decrypted_flow_cell.stem).stem
        LOG.debug(f"Extraction target dir: {extraction_target_dir}")

        start_time = get_start_time()

        try:
            self.pdc.retrieve_encryption_key(
                encryption_key=str(encrypted_key),
                root_dir=str(root_dir),
                dry_run=dry_run,
            )
            if not dry_run:
                flow_cell_obj.status = FlowCellStatus.RETRIEVED
                self.status.commit()
                LOG.info(
                    "Status for flow cell %s set to %s", flow_cell_obj.name, flow_cell_obj.status
                )
        except subprocess.CalledProcessError as error:
            if error.returncode == RETURN_WARNING:
                LOG.warning(
                    "WARNING for retrieval of encryption key of flow cell %s, please check "
                    "dsmerror.log",
                    flow_cell_obj.name,
                )
            else:
                LOG.error("%s: retrieval failed", flow_cell_obj.name)
                if not dry_run:
                    flow_cell_obj.status = FlowCellStatus.REQUESTED
                    self.status.commit()
                raise error
        try:
            self.pdc.retrieve_flow_cell(
                flow_cell=str(archived_flow_cell),
                root_dir=str(root_dir),
                dry_run=dry_run,
            )
            if not dry_run:
                flow_cell_obj.status = FlowCellStatus.RETRIEVED
                self.status.commit()
                LOG.info(
                    "Status for flow cell %s set to %s", flow_cell_obj.name, flow_cell_obj.status
                )
        except subprocess.CalledProcessError as error:
            if error.returncode == RETURN_WARNING:
                LOG.warning(
                    "WARNING for retrieval of flow cell %s, please check dsmerror.log",
                    flow_cell_obj.name,
                )
            else:
                LOG.error("%s: retrieval failed", flow_cell_obj.name)
                if not dry_run:
                    flow_cell_obj.status = FlowCellStatus.REQUESTED
                    self.status.commit()
                raise error
        try:
            decryption_command = self.encryption_api.get_asymmetric_decryption_command(
                input_file=encrypted_key, output_file=encryption_key
            )
            LOG.debug(f"Decrypt key command: {decryption_command}")
            self.encryption_api.run_gpg_command(decryption_command)

            decryption_command = self.encryption_api.get_symmetric_decryption_command(
                input_file=archived_flow_cell,
                output_file=decrypted_flow_cell,
                encryption_key=encryption_key,
            )
            LOG.debug(f"Decrypt flow cell command: {decryption_command}")
            self.encryption_api.run_gpg_command(decryption_command)

            extraction_command = self.tar_api.get_extract_file_command(
                input_file=decrypted_flow_cell, output_dir=root_dir
            )
            LOG.debug(f"Extract flow cell command: {extraction_command}")
            self.encryption_api.run_gpg_command(extraction_command)
            (extraction_target_dir / DemultiplexingDirsAndFiles.RTACOMPLETE).touch()
            LOG.debug(f"Unlink files")
            archived_flow_cell.unlink()
            decrypted_flow_cell.unlink()
            encrypted_key.unlink()
            encryption_key.unlink()
        except subprocess.CalledProcessError as error:
            LOG.error("Decryption failed: %s", error.stderr)
            return

        return get_elapsed_time(start_time=start_time)

    @staticmethod
    def get_archived_flow_cell(query: list) -> Path:
        """Get the path of the archived flow cell from a PDC query"""
        flow_cell_query: str = [
            row
            for row in query
            if FileExtensions.TAR in row
            and FileExtensions.GZIP in row
            and FileExtensions.GPG in row
        ][ListIndexes.FIRST.value]
        return Path(flow_cell_query.split(SPACE)[ListIndexes.PDC_FC_COLUMN.value])

    @staticmethod
    def get_archived_encryption_key(query: list) -> Path:
        """Get the encryption key for the archived flow cell from a PDC query"""

        encryption_key_query: str = [
            row for row in query if FileExtensions.KEY in row and FileExtensions.GPG in row
        ][ListIndexes.FIRST.value]
        return Path(encryption_key_query.split(SPACE)[ListIndexes.PDC_KEY_COLUMN.value])

    def query_pdc_for_flow_cell(self, flow_cell_id) -> list:
        """Query PDC for a given flow cell id"""
        search_pattern = EncryptionDirsAndFiles.ENCRYPT_DIR + ASTERISK + flow_cell_id + ASTERISK
        self.pdc.query_pdc(search_pattern=search_pattern)
        query: list = self.pdc.process.stdout.split(NEW_LINE)
        return query

    @staticmethod
    def get_target_path(root_dir: str, file_: str) -> str:
        """Determines the target path for PDC retrieval"""
        return str(Path(root_dir) / Path(file_).name)


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
        self._dry_run = dry_run

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
            LOG.error(error.message)
            self.encryption_api.cleanup(spring_file_path)
            LOG.debug(f"*** CHECKSUM PROCESS FAILED! ***")

    def retrieve_and_decrypt_spring_file(self, spring_file_path: Path) -> None:
        """Retrieves and decrypts a spring file and its decryption key"""
        LOG.info(f"*** START RETRIEVAL PROCESS OF SPRING FILE %s ***", spring_file_path)
        try:
            self.pdc.retrieve_file_from_pdc(
                file_path=str(self.encryption_api.encrypted_spring_file_path(spring_file_path)),
                dry_run=self.dry_run,
            )
            self.pdc.retrieve_file_from_pdc(
                file_path=str(self.encryption_api.encrypted_key_path(spring_file_path)),
                dry_run=self.dry_run,
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

    @property
    def dry_run(self) -> bool:
        """Dry run property"""
        LOG.debug("Backup dry run property: %s", self._dry_run)
        return self._dry_run

    @dry_run.setter
    def dry_run(self, value: bool) -> None:
        """Set the dry run property"""
        LOG.debug(
            "Set backup dry run property to %s, and set the encryption dry run property to the "
            "same value",
            value,
        )
        self._dry_run = value
        self.encryption_api.dry_run = value

    def is_spring_file_archived(self, spring_file_path: Path) -> bool:
        """Checks if a spring file is marked as archived in Housekeeper"""
        return self.hk_api.files(path=str(spring_file_path)).first().to_archive

    @staticmethod
    def is_compression_ongoing(spring_file_path: Path) -> bool:
        """Determines if (de)compression of the spring file ongoing"""
        return CompressionData(spring_file_path).pending_exists()
