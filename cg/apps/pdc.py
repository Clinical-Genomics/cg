import logging
import subprocess

LOG = logging.getLogger(__name__)


class PdcApi():

    def __init__(self, config: dict):
        pass

    def retrieve_flowcell(self, flowcell_id: str, sequencer_type: str) -> str:
        """Fetch a flowcell back from the backup solution."""
        dest_server = {
            'hiseqga': 'thalamus',
            'hiseqx': 'hasta',
        }.get(sequencer_type)
        if dest_server is None:
            raise ValueError(f"{sequencer_type}: invalid sequencer type")

        bash_command = f"bash SCRIPTS/retrieve_run_nas.bash {flowcell_id} {dest_server}"
        command = ['ssh', 'nas-9.scilifelab.se', bash_command]
        LOG.info(' '.join(command))
        subprocess.check_call(command)
