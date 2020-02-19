import logging
import subprocess

LOG = logging.getLogger(__name__)


class PdcApi():

    def __init__(self, config: dict):
        pass

    def retrieve_flowcell(self, flowcell_id: str, sequencer_type: str) -> str:
        """Fetch a flowcell back from the backup solution."""
        server, path = {
            'novaseq': ('thalamus', '/home/hiseq.clinical/novaseq/runs/'),
            'hiseqga': ('thalamus', '/home/hiseq.clinica/RUNS/'),
            'hiseqx': ('hasta', '/home/proj/production/flowcells/hiseqx/'),
        }.get(sequencer_type)
        if server is None:
            raise ValueError(f"{sequencer_type}: invalid sequencer type")

        bash_command = f"bash SCRIPTS/retrieve_run_nas.bash {flowcell_id} {server} {path}"
        command = ['ssh', 'nas-9.scilifelab.se', bash_command]
        LOG.info(' '.join(command))
        subprocess.check_call(command)
