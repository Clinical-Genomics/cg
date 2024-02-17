""" Module to group PDC related commands."""

import logging
from pathlib import Path
from subprocess import CalledProcessError

import psutil

from cg.constants.pdc import DSMCParameters
from cg.constants.process import EXIT_WARNING
from cg.exc import (
    DsmcAlreadyRunningError,
    FlowCellAlreadyBackedUpError,
    FlowCellEncryptionError,
    PdcError,
)
from cg.meta.encryption.encryption import FlowCellEncryptionAPI
from cg.store.models import Flowcell
from cg.store.store import Store
from cg.utils import Process

LOG = logging.getLogger(__name__)

SERVER = "hasta"
NO_FILE_FOUND_ANSWER = "ANS1092W"
MAX_NR_OF_DSMC_PROCESSES: int = 3


class PdcAPI:
    """Group PDC related commands"""

    def __init__(self, binary_path: str, dry_run: bool = False):
        self.process: Process = Process(binary=binary_path)
        self.dry_run: bool = dry_run

    @classmethod
    def validate_is_dsmc_running(cls) -> bool:
        """Check if a Dsmc process is already running on the system.
        Raises:
            Exception: for all non-exit exceptions.
        """
        is_dsmc_running: bool = False
        dsmc_process_count: int = 0
        try:
            for process in psutil.process_iter():
                if "dsmc" == process.name():
                    dsmc_process_count += 1
        except Exception as error:
            LOG.debug(f"{error}")
        if dsmc_process_count >= MAX_NR_OF_DSMC_PROCESSES:
            is_dsmc_running = True
            LOG.debug("Too many Dsmc processes are already running")
        return is_dsmc_running

    def archive_file_to_pdc(self, file_path: str) -> None:
        """Archive a file by storing it on PDC."""
        if not self.dry_run:
            self.run_dsmc_command(command=DSMCParameters.ARCHIVE_COMMAND + [file_path])

    def query_pdc(self, search_pattern: str) -> None:
        """Query PDC based on a given search pattern."""
        command: list = DSMCParameters.QUERY_COMMAND.copy()
        command.append(search_pattern)
        self.run_dsmc_command(command=command)

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
        except CalledProcessError as error:
            if error.returncode == EXIT_WARNING:
                LOG.warning(f"{error}")
                return
            raise PdcError(message=f"{error}") from error

    def validate_is_flow_cell_backup_possible(
        self, db_flow_cell: Flowcell, flow_cell_encryption_api: FlowCellEncryptionAPI
    ) -> bool:
        """Check if back-up of flow cell is possible.
        Raises:
            DsmcAlreadyRunningError if there is already a Dsmc process ongoing.
            FlowCellAlreadyBackupError if flow cell is already backed up.
            FlowCellEncryptionError if encryption is not complete.
        """
        if self.validate_is_dsmc_running():
            raise DsmcAlreadyRunningError("Too many Dsmc processes are already running")
        if db_flow_cell and db_flow_cell.has_backup:
            raise FlowCellAlreadyBackedUpError(
                f"Flow cell: {db_flow_cell.name} is already backed-up"
            )
        if not flow_cell_encryption_api.complete_file_path.exists():
            raise FlowCellEncryptionError(
                f"Flow cell: {flow_cell_encryption_api.flow_cell.id} encryption process is not complete"
            )
        LOG.debug("Flow cell can be backed up")

    def backup_flow_cell(
        self, files_to_archive: list[Path], store: Store, db_flow_cell: Flowcell
    ) -> None:
        """Back-up flow cell files."""
        for encrypted_file in files_to_archive:
            if not self.dry_run:
                self.archive_file_to_pdc(file_path=encrypted_file.as_posix())
        if not self.dry_run:
            store.update_flow_cell_has_backup(flow_cell=db_flow_cell, has_backup=True)
            LOG.info(f"Flow cell: {db_flow_cell.name} has been backed up")

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

    @staticmethod
    def was_file_found(dsmc_output: str) -> bool:
        """Check if file was found in PDC."""
        return NO_FILE_FOUND_ANSWER not in dsmc_output
