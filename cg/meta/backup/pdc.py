""" Module to group PDC related commands """

import logging
from pathlib import Path

from cg.constants.pdc import DSMCParameters
from cg.utils import Process

LOG = logging.getLogger(__name__)

SERVER = "hasta"


class PdcAPI:
    """Group PDC related commands"""

    def __init__(self, binary_path: str = None):
        self.process: Process = Process(binary=binary_path)

    def retrieve_flow_cell(self, flow_cell: str, root_dir: str, dry_run: bool = False) -> None:
        """Fetch a flow cell from the backup solution"""
        flow_cell_target: str = self.get_target_path(root_dir=root_dir, file_=flow_cell)
        LOG.debug(f"Flow cell key target: {flow_cell_target}")

        self.retrieve_file_from_pdc(
            file_path=flow_cell, target_path=flow_cell_target, dry_run=dry_run
        )

    def retrieve_encryption_key(
        self, encryption_key: str, root_dir: str, dry_run: bool = False
    ) -> None:
        """Fetch an encryption key from the backup solution"""
        encryption_key_target: str = self.get_target_path(root_dir=root_dir, file_=encryption_key)
        LOG.debug(f"Encryption key target: {encryption_key_target}")

        self.retrieve_file_from_pdc(
            file_path=encryption_key, target_path=encryption_key_target, dry_run=dry_run
        )

    def archive_file_to_pdc(self, file_path: str, dry_run: bool = False) -> None:
        """Archive a file by storing it on PDC"""
        command: list = DSMCParameters.ARCHIVE_COMMAND.copy()
        command.append(file_path)
        if not dry_run:
            self.run_dsmc_command(command=command, dry_run=dry_run)

    def query_pdc(self, search_pattern: str, dry_run: bool = False) -> None:
        """Query PDC based on a given search pattern"""
        command: list = DSMCParameters.QUERY_COMMAND.copy()
        command.append(search_pattern)
        self.run_dsmc_command(command=command, dry_run=dry_run)

    def retrieve_file_from_pdc(
        self, file_path: str, target_path: str, dry_run: bool = False
    ) -> None:
        """Retrieve a file from PDC"""
        command: list = DSMCParameters.RETRIEVE_COMMAND.copy()
        command.append(file_path)
        if target_path:
            command.append(target_path)
        self.run_dsmc_command(command=command, dry_run=dry_run)

    def run_dsmc_command(self, command: list, dry_run: bool = False) -> None:
        """Runs a DSMC command"""
        LOG.debug("Starting DSMC command:")
        LOG.debug(f"{self.process.binary} {' '.join(command)}")
        self.process.run_command(parameters=command, dry_run=dry_run)
