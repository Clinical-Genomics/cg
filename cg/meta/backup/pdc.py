""" Module to group PDC related commands """

import logging

import psutil

from cg.constants.pdc import DSMCParameters
from cg.exc import PdcError
from cg.utils import Process

LOG = logging.getLogger(__name__)

SERVER = "hasta"


class PdcAPI:
    """Group PDC related commands"""

    def __init__(self, binary_path: str = None, dry_run: bool = False):
        self.process: Process = Process(binary=binary_path)
        self.dry_run: bool = dry_run

    def is_dcms_running(self) -> bool:
        """Check if a dmcs process is already running on the system."""
        is_dcms_running: bool = False
        try:
            for process in psutil.process_iter():
                if "dsmc" in process.name():
                    is_dcms_running = True
        except Exception as error:
            LOG.debug(f"{error}")
        if is_dcms_running:
            LOG.info("A Dcms process is already running")
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
        """Runs a DSMC command"""
        LOG.debug("Starting DSMC command:")
        LOG.debug(f"{self.process.binary} {' '.join(command)}")
        try:
            self.process.run_command(parameters=command, dry_run=self.dry_run)
        except Exception as error:
            raise PdcError(f"{error}")
