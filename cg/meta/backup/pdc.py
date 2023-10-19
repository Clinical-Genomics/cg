""" Module to group PDC related commands """

import logging
from pathlib import Path

import psutil

from cg.constants.pdc import DSMCParameters
from cg.exc import (
    DcmsAlreadyRunningError,
    FlowCellAlreadyBackedUpError,
    FlowCellEncryptionError,
    PdcError,
)
from cg.meta.encryption.encryption import FlowCellEncryptionAPI
from cg.store import Store
from cg.store.models import Flowcell
from cg.utils import Process

LOG = logging.getLogger(__name__)

SERVER = "hasta"


class PdcAPI:
    """Group PDC related commands"""

    def __init__(self, binary_path: str = None, dry_run: bool = False):
        self.process: Process = Process(binary=binary_path)
        self.dry_run: bool = dry_run

    def validate_is_dcms_running(self) -> bool:
        """Check if a dmcs process is already running on the system.
        Raises:
            Exception: for all non-exit exceptions.
        """
        is_dcms_running: bool = False
        try:
            for process in psutil.process_iter():
                if "dsmc" in process.name():
                    is_dcms_running = True
        except Exception as error:
            LOG.debug(f"{error}")
        if is_dcms_running:
            LOG.debug("A Dcms process is already running")
        return is_dcms_running

    def archive_file_to_pdc(self, file_path: str, dry_run: bool = False) -> None:
        """Archive a file by storing it on PDC"""
        command: list = DSMCParameters.ARCHIVE_COMMAND.copy()
        command.append(file_path)
        if not dry_run:
            self.run_dsmc_command(command=command)

    def query_pdc(self, search_pattern: str) -> None:
        """Query PDC based on a given search pattern."""
        command: list = DSMCParameters.QUERY_COMMAND.copy()
        command.append(search_pattern)
        LOG.debug("Starting DSMC command:")
        LOG.debug(f"{self.process.binary} {' '.join(command)}")
        self.process.run_command(parameters=command)

    def retrieve_file_from_pdc(self, file_path: str, target_path: str = None) -> None:
        """Retrieve a file from PDC"""
        command: list = DSMCParameters.RETRIEVE_COMMAND.copy()
        command.append(file_path)
        if target_path:
            command.append(target_path)
        self.run_dsmc_command(command=command)

    def run_dsmc_command(self, command: list) -> None:
        """Runs a DSMC command.
        Raises:
            PdcError when unable to process command.
        """
        LOG.debug("Starting DSMC command:")
        LOG.debug(f"{self.process.binary} {' '.join(command)}")
        try:
            self.process.run_command(parameters=command, dry_run=self.dry_run)
        except Exception as error:
            raise PdcError(f"{error}") from error

    def validate_is_flow_cell_backup_possible(
        self, db_flow_cell: Flowcell, flow_cell_encryption_api: FlowCellEncryptionAPI
    ) -> bool:
        """Check if back-up of flow cell is possible.
        Raises:
            DcmsAlreadyRunningError if there is already a Dcms process ongoing
            FlowCellAlreadyBackupError if flow cell is already backed up
            FlowCellEncryptionError if encryption is not complete
        """
        if self.validate_is_dcms_running():
            raise DcmsAlreadyRunningError("A Dcms process is already running")
        if db_flow_cell and db_flow_cell.has_backup:
            raise FlowCellAlreadyBackedUpError(
                f"Flow cell: {db_flow_cell.name} is already backed-up"
            )
        if not flow_cell_encryption_api.complete_file_path.exists():
            raise FlowCellEncryptionError(
                f"Flow cell: {flow_cell_encryption_api.flow_cell.id} encryption process is not complete"
            )
        return True

    def backup_flow_cell(
        self, files_to_archive: list[Path], store: Store, db_flow_cell: Flowcell
    ) -> None:
        """Back-up flow cell files."""
        archived_file_count: int = 0
        for encrypted_file in files_to_archive:
            try:
                self.archive_file_to_pdc(file_path=encrypted_file.as_posix())
                archived_file_count += 1
            except PdcError:
                LOG.debug(f"{encrypted_file.as_posix()} cannot be archived")
            if archived_file_count == len(files_to_archive) and not self.dry_run:
                store.update_flow_cell_has_backup(flow_cell=db_flow_cell, has_backup=True)
                LOG.debug(f"Flow cell: {db_flow_cell.name} has been backed up")

    def start_flow_cell_backup(
        self,
        db_flow_cell: Flowcell,
        flow_cell_encryption_api: FlowCellEncryptionAPI,
        status_db: Store,
    ) -> None:
        """Check if back-up of flow cell is possible and if so starts it."""
        self.validate_is_flow_cell_backup_possible(
            db_flow_cell=db_flow_cell, flow_cell_encryption_api=flow_cell_encryption_api
        )
        self.backup_flow_cell(
            files_to_archive=[
                flow_cell_encryption_api.final_passphrase_file_path,
                flow_cell_encryption_api.encrypted_gpg_file_path,
            ],
            store=status_db,
            db_flow_cell=db_flow_cell,
        )
