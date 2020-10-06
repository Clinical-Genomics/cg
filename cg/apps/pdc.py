""" Module to group PDC related commands """

import logging
import subprocess

LOG = logging.getLogger(__name__)


class PdcApi:
    """ Group PDC related commands """

    @classmethod
    def retrieve_flowcell(
        cls, flowcell_id: str, sequencer_type: str, root_dir: str, dry: bool = False
    ) -> str:
        """Fetch a flowcell back from the backup solution."""
        server = {
            "novaseq": "thalamus",
            "hiseqga": "thalamus",
            "hiseqx": "hasta",
        }.get(sequencer_type)
        path = root_dir[sequencer_type]

        if server is None:
            raise ValueError(f"{sequencer_type}: invalid sequencer type")

        bash_command = f"bash SCRIPTS/retrieve_run_nas.bash {flowcell_id} {server} {path}"
        command = ["ssh", "nas-9.scilifelab.se", bash_command]
        LOG.info(" ".join(command))
        if not dry:
            subprocess.check_call(command)
