""" Module to group PDC related commands """

import logging
import subprocess

from cg.constants.pdc import DSMCParameters
from cg.utils import Process

LOG = logging.getLogger(__name__)

SERVER = "hasta"


class PdcAPI:
    """Group PDC related commands"""

    def __init__(self, binary_path: str = None):
        self.process: Process = Process(binary=binary_path)

    @classmethod
    def retrieve_flow_cell(
        cls, flow_cell_id: str, sequencer_type: str, root_dir: dict, dry: bool = False
    ) -> None:
        """Fetch a flow cell back from the backup solution."""
        path = root_dir[sequencer_type]
        bash_command = f"bash SCRIPTS/retrieve_run_nas.bash {flow_cell_id} {SERVER} {path}"
        command = ["ssh", "nas-9.scilifelab.se", bash_command]
        LOG.info(" ".join(command))
        if not dry:
            subprocess.check_call(command)

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

    def retrieve_file_from_pdc(self, file_path: str, dry_run: bool = False) -> None:
        """Retrieve a file from PDC"""
        command: list = DSMCParameters.RETRIEVE_COMMAND.copy()
        command.append(file_path)
        self.run_dsmc_command(command=command, dry_run=dry_run)

    def run_dsmc_command(self, command: list, dry_run: bool = False) -> None:
        """Runs a DSMC command"""
        LOG.debug("Starting DSMC command:")
        LOG.debug(f"{self.process.binary} {' '.join(command)}")
        self.process.run_command(parameters=command, dry_run=dry_run)
