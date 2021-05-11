"""Parse statistics from the demultiplexing stats file"""
import logging
from pathlib import Path
from typing import Dict, Optional, Set
from xml.etree.ElementTree import Element, iterparse

from pydantic import BaseModel

LOG = logging.getLogger(__name__)


class SampleBarcodeStats(BaseModel):
    barcode_count: int
    perfect_barcode_count: int
    one_mismatch_barcode_count: Optional[int]


class DemuxStats:
    def __init__(self, demux_stats_path: Path):
        self.demux_stats_path: Path = demux_stats_path
        self._current_project = ""
        self._current_sample = ""
        self._current_barcode = ""
        self._current_lane: int = 0
        self._current_barcode_count = 0
        self._current_perfect_barcode_count = 0
        self._current_mismatch_barcode_count = 0
        self._skip_entry: bool = False
        self.flowcell_id = ""
        self.projects: Set[str] = set()
        self.samples: Set[str] = set()
        self.barcodes: Set[str] = set()
        self.barcode_to_sample: Dict[str, str] = {}
        self.lanes: Set[int] = set()
        self.lanes_to_barcode = {}
        self.barcode_to_lanes = {}
        self.parse_file()

    def create_entry(self) -> None:
        """Create a entry of SampleBarcodeStats and add it in a structured way"""
        entry: SampleBarcodeStats = SampleBarcodeStats(
            barcode_count=self._current_barcode_count,
            perfect_barcode_count=self._current_perfect_barcode_count,
            one_mismatch_barcode_count=self._current_mismatch_barcode_count,
        )
        LOG.debug("Creating entry %s", entry)
        if self._current_lane not in self.lanes_to_barcode:
            self.lanes_to_barcode[self._current_lane] = {}
        self.lanes_to_barcode[self._current_lane][self._current_barcode] = entry
        if self._current_barcode not in self.barcode_to_lanes:
            self.barcode_to_lanes[self._current_barcode] = {}
        self.barcode_to_lanes[self._current_barcode][self._current_lane] = entry

    def parse_file(self) -> None:
        """Parse a XML file with demux statistics"""
        LOG.info("Parsing demux stats file %s", self.demux_stats_path)
        for (event, node) in iterparse(str(self.demux_stats_path), ["start", "end"]):
            if event == "start":
                self.evaluate_start_event(node)
                continue
            if not self._skip_entry:
                self.evaluate_end_event(node)
            node.clear()

    def evaluate_start_event(self, node: Element) -> None:
        """Check what type a start event is and take the relevant action depending on type"""
        if node.tag == "Flowcell":
            self.set_flowcell_id(node)
        elif node.tag == "Project":
            self.set_project(node)
        elif node.tag == "Sample":
            if node.attrib["name"].lower() in ["all", "undetermined"]:
                self._skip_entry = True
                LOG.debug("Skip sample %s" % node.attrib["name"])
            self._skip_entry = False
            self.set_current_sample(node)
        elif node.tag == "Barcode":
            # Skip the barcode="All"
            if node.attrib["name"].lower() == "all":
                self._skip_entry = True
                return
            self._skip_entry = False
            self.set_current_barcode(node)
        elif node.tag == "Lane":
            self.set_current_lane(node)

    def evaluate_end_event(self, node: Element) -> None:
        """Check what type a end event is and take the relevant action depending on type"""
        # These needs to operate on end tags to ensure value exists
        if node.tag == "BarcodeCount":
            self._current_barcode_count = int(node.text)
        elif node.tag == "PerfectBarcodeCount":
            self._current_perfect_barcode_count = int(node.text.strip())
        elif node.tag == "OneMismatchBarcodeCount":
            self._current_mismatch_barcode_count = int(node.text)
        elif node.tag == "Lane":
            self.create_entry()

    def set_current_lane(self, node: Element) -> None:
        lane: int = int(node.attrib["number"].strip())
        LOG.debug("Set current lane to %s", lane)
        self._current_lane = lane
        self.lanes.add(lane)

    def set_current_barcode(self, node: Element) -> None:
        barcode_id = node.attrib["name"].strip()
        LOG.debug("Set current barcode %s", barcode_id)
        self._current_barcode = barcode_id
        self.barcodes.add(barcode_id)
        self.barcode_to_sample[barcode_id] = self._current_sample

    def set_current_sample(self, node: Element) -> None:
        sample_id = node.attrib["name"].strip()
        LOG.debug("Set current sample to %s", sample_id)
        self._current_sample = sample_id
        self.samples.add(sample_id)

    def set_project(self, node: Element) -> None:
        project: str = node.attrib["name"].strip()
        LOG.debug("Set current project to %s", project)
        self._current_project = project
        self.projects.add(project)

    def set_flowcell_id(self, node: Element) -> None:
        flowcell = node.attrib["flowcell-id"].strip()
        LOG.debug("Set flowcell id to %s", flowcell)
        self.flowcell_id = flowcell

    def __repr__(self):
        return (
            f"DemuxStats(flowcell_id={self.flowcell_id},projects={self.projects},lanes={self.lanes}"
        )
