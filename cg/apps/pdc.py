""" Module to group PDC related commands """

import logging
import subprocess

LOG = logging.getLogger(__name__)

SERVER = "hasta"


class PdcApi:
    """Group PDC related commands"""

    @classmethod
    def retrieve_flowcell(
        cls, flowcell_id: str, sequencer_type: str, root_dir: dict, dry: bool = False
    ) -> None:
        """Fetch a flowcell back from the backup solution."""
        path = root_dir[sequencer_type]
        bash_command = f"bash SCRIPTS/retrieve_run_nas.bash {flowcell_id} {SERVER} {path}"
        command = ["ssh", "nas-9.scilifelab.se", bash_command]
        LOG.info(" ".join(command))
        if not dry:
            subprocess.check_call(command)
