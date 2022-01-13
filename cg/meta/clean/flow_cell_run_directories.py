"""Module that handles deletion of flow cell run directories and their BCL files from
/home/proj/production/flowcells/<sequencer> """
import logging
from pathlib import Path

LOG = logging.getLogger(__name__)


class CleanAPI:
    """ """

    def __init__(self, sequencer: str, flow_cell_dir: str):
        self.sequencer: str = sequencer
        self.flowcell_dir: Path = Path(flow_cell_dir)
