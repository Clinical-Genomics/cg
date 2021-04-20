"""Parse statistics from the demultiplexing stats file"""
import logging
from pathlib import Path
from pprint import pprint as pp
from typing import Dict, Optional, Set
from xml.etree.ElementTree import Element, iterparse

from pydantic import BaseModel

LOG = logging.getLogger(__name__)


class LaneResults(BaseModel):
    barcode_count: int
    perfect_barcode_count: int
    one_mismatch_barcode_count: Optional[int]


class DemuxStats:
    def __init__(self, stats_file: Path):
        self.stats_file: Path = stats_file
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

    def create_entry(self):
        entry: LaneResults = LaneResults(
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

    def parse_file(self):
        line_nr: int = 0
        for (event, node) in iterparse(str(self.stats_file), ["start", "end"]):
            line_nr += 1
            if node.tag == "Lane" and event == "end":
                if self._skip_entry:
                    continue
                self.create_entry()
                continue
            self.evaluate_node(node, event)

    def evaluate_node(self, node: Element, event: str):
        # Only search nodes when correct
        if node.tag == "Flowcell" and event == "start":
            self.set_flowcell_id(node)
        if node.tag == "Project" and event == "start":
            self.set_project(node)
        if node.tag == "Sample" and event == "start":
            if node.attrib["name"].lower() in ["all", "undetermined"]:
                self._skip_entry = True
                LOG.debug("Skip sample %s" % node.attrib["name"])
            self._skip_entry = False
            self.set_current_sample(node)
        if self._skip_entry:
            return
        if node.tag == "Barcode" and event == "start":
            # Skip the barcode="All"
            if node.attrib["name"].lower() == "all":
                self._skip_entry = True
                return
            self._skip_entry = False
            self.set_current_barcode(node)
        if self._skip_entry:
            return

        elif node.tag == "Lane" and event == "start":
            self.set_current_lane(node)
        # These needs to operate on end tags to ensure value exists
        elif node.tag == "BarcodeCount" and event == "end":
            self._current_barcode_count = int(node.text)
        elif node.tag == "PerfectBarcodeCount" and event == "end":
            self._current_perfect_barcode_count = int(node.text.strip())
        elif node.tag == "OneMismatchBarcodeCount" and event == "end":
            self._current_mismatch_barcode_count = int(node.text)

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


if __name__ == "__main__":
    xml_file = Path("/Users/mans.magnusson/PycharmProjects/cg/local/DemultiplexingStats.xml")
    parser = DemuxStats(stats_file=xml_file)
    parser.parse_file()
    print(parser)
    pp(parser.barcode_to_lanes)
    # barcode_count: dict = get_barcode_count(
    #    xml_path=xml_file,
    #    project_name="150392",
    #    barcode_name="CTATAGCGAG+AGTCGACTAG",
    #    lane_number=1,
    # )
    # from pprint import pprint as pp
    #
    # pp(barcode_count)
    # barcode_name = "AACACAGCCG+AGACCTTGGT"
    # lane_number = 1
    # xml_file = Path("/Users/mans.magnusson/PycharmProjects/cg/local/ConversionStats.xml")
    # get_cluster_values(
    #     xml_path=xml_file,
    #     project_name="150392",
    #     barcode_name=barcode_name,
    #     lane_number=lane_number,
    # )
    # print(node.tag, node.attrib)
    # nr_tiles: int = 0
    # for nr_tiles, child in enumerate(
    #     node.iterfind(
    #         f"./Sample/Barcode[@name='{barcode_name}']/Lane[@number='{lane_number}']/Tile/Raw/ClusterCount"
    #     )
    # ):
    #     print(child.text)
    # print(nr_tiles)
