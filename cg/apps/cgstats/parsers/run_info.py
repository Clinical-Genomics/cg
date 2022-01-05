""" Parse information fror RunInfo.xml"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path

LOG = logging.getLogger(__name__)


class RunInfo:
    def __init__(self, runinfo_path: Path):
        self.runinfo_path = runinfo_path
        self.root = self.parse_file()

    def parse_file(self) -> ET.Element:
        """Parse the file RunInfo.xml"""
        LOG.info("Parsing demux conversion stats file %s", self.runinfo_path)
        tree = ET.parse(self.runinfo_path)
        return tree.getroot()

    @property
    def read_length(self) -> int:
        """Get the read length for this flowcell"""
        return int(self.root.find("Run/Reads/Read").attrib["NumCycles"])
