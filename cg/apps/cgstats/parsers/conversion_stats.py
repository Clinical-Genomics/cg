"""
Parse statistics from the demultiplexing conversion stats file

File is ordered like
Flowcell
  Project
    Sample
      Barcode
        Lane
         Tile
           Raw
             ClusterCount
             Read nr1
             Read nr2
           Pf (passed filter)
             ClusterCount
             Read nr1
             Read nr2


There are many tiles for each lane. We are not interested about the tile level but want to add upp the information to
lane level, just like we do in the demux stats.
"""
import copy
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from xml.etree.ElementTree import Element, iterparse

from pydantic import BaseModel

LOG = logging.getLogger(__name__)


class SampleConversionResults(BaseModel):
    """Class to collect the demultiplexing conversion results for a sample on a lane"""

    raw_cluster_count: int = 0
    raw_yield: int = 0
    pass_filter_cluster_count: int = 0
    pass_filter_read1_yield: int = 0
    pass_filter_read2_yield: int = 0
    pass_filter_yield: int = 0
    pass_filter_q30: int = 0
    pass_filter_read1_q30: int = 0
    pass_filter_read2_q30: int = 0
    pass_filter_quality_score_sum: int = 0
    pass_filter_quality_score: float = 0
    barcode: str = ""
    sample_id: str = ""


class UnknownBarcode(BaseModel):
    barcode: str
    read_count: int


class ConversionStats:
    def __init__(self, conversion_stats_path: Path):
        self.conversion_stats_path: Path = conversion_stats_path
        self._current_sample = ""
        self._current_barcode = ""
        self._results: SampleConversionResults = SampleConversionResults()
        self._skip_entry: bool = False
        self._current_lane: int = 0
        self.unknown_barcodes_entry: bool = False
        # Keep track where we are in the xml file
        self.current_path: List[str] = []
        self.flowcell_id = ""
        self.projects: Set[str] = set()
        self.samples: Set[str] = set()
        self.barcodes: Set[str] = set()
        self.barcode_to_sample: Dict[str, str] = {}
        self.lanes: Set[int] = set()
        self.unknown_barcodes: List[UnknownBarcode] = []
        # Mapping from lane to barcodes and the results
        self.lanes_to_barcode: Dict[int, Dict[str, SampleConversionResults]] = {}
        self.barcode_to_lanes: Dict[str, Dict[int, SampleConversionResults]] = {}
        self.lanes_to_unknown_barcode: Dict[int, List[UnknownBarcode]] = {}
        # This is just a summary of all raw clusters per lane
        self.raw_clusters_per_lane: Dict[int, int] = {}
        self.parse_file()

    @staticmethod
    def get_current_tag(node: Element) -> str:
        current_tag = node.tag
        if current_tag == "Read":
            read_number = "1" if node.attrib["number"] == "1" else "2"
            current_tag = "_".join(["Read", read_number])
        return current_tag

    def parse_file(self) -> None:
        """Parse a file with demux conversion stats information"""
        event: str
        node: Element
        LOG.info("Parsing demux conversion stats file %s", self.conversion_stats_path)
        for (event, node) in iterparse(str(self.conversion_stats_path), ["start", "end"]):
            # Only search nodes when correct
            # print("Path", self.current_path, self._current_barcode)
            current_tag: str = self.get_current_tag(node=node)
            if event == "start":
                self.evaluate_start_event(node=node, current_tag=current_tag)
                continue

            if not self._skip_entry:
                self.evaluate_end_event(node=node, current_tag=current_tag)
            # Remove closed event from current path
            self.current_path.pop()
            # Release element tree from memory
            node.clear()

    @staticmethod
    def update_quality_score(entry: SampleConversionResults) -> None:
        """Calculate the quality score for the lane results"""
        if not entry.pass_filter_yield:
            LOG.debug("Could not find pass filter yield")
            return
        quality_score: float = entry.pass_filter_quality_score_sum / entry.pass_filter_yield
        LOG.debug("Set pass filter quality score to %s", quality_score)
        entry.pass_filter_quality_score = quality_score

    @staticmethod
    def update_summaries(entry: SampleConversionResults) -> None:
        entry.pass_filter_q30 = entry.pass_filter_read1_q30 + entry.pass_filter_read2_q30
        entry.pass_filter_yield = entry.pass_filter_read1_yield + entry.pass_filter_read2_yield

    def update_lane_clusters(self, entry: SampleConversionResults) -> None:
        if self._current_lane not in self.raw_clusters_per_lane:
            self.raw_clusters_per_lane[self._current_lane] = 0
        self.raw_clusters_per_lane[self._current_lane] += entry.raw_cluster_count

    def create_entry(self) -> None:
        entry: SampleConversionResults = copy.deepcopy(self._results)
        self.update_summaries(entry)
        self.update_quality_score(entry)
        self.update_lane_clusters(entry)
        entry.barcode = self._current_barcode
        entry.sample_id = self._current_sample
        if self._current_lane not in self.lanes_to_barcode:
            self.lanes_to_barcode[self._current_lane] = {}
        self.lanes_to_barcode[self._current_lane][self._current_barcode] = entry
        if self._current_barcode not in self.barcode_to_lanes:
            self.barcode_to_lanes[self._current_barcode] = {}
        self.barcode_to_lanes[self._current_barcode][self._current_lane] = entry
        LOG.debug("Adding entry %s for barcode %s", entry, self._current_barcode)
        LOG.debug("Reset conversion results")
        self._results = SampleConversionResults()

    def create_unknown_barcodes_entry(self) -> None:
        LOG.debug("Creating unknown barcode entry for lane %s", self._current_lane)
        lane_results: List[UnknownBarcode] = copy.deepcopy(self.unknown_barcodes)
        self.lanes_to_unknown_barcode[self._current_lane] = lane_results
        self.unknown_barcodes = []
        self.unknown_barcodes_entry = False

    def evaluate_start_event(self, node: Element, current_tag: str) -> None:
        # print("Start!", current_tag, node, node.attrib, node.text)

        LOG.debug("Add start event %s to current path", current_tag)
        self.current_path.append(current_tag)
        if current_tag == "Lane":
            self.set_current_lane(lane_nr=int(node.attrib["number"]))
        elif current_tag == "Sample":
            sample_name: str = node.attrib["name"]
            if "indexcheck" in sample_name:
                self._skip_entry = True
                LOG.debug("Skip indexcheck sample %s" % sample_name)
                return
            if sample_name.lower() in ["all", "undetermined"]:
                self._skip_entry = True
                LOG.debug("Skip sample %s" % sample_name)
                return
            self._skip_entry = False
            self.set_current_sample(sample_name=sample_name)
        elif current_tag == "Barcode":
            if self.unknown_barcodes_entry:
                unknown_barcode = UnknownBarcode(
                    barcode=node.attrib.get("sequence"), read_count=int(node.attrib.get("count"))
                )
                LOG.debug("Creating unknown barcodes entry for %s", unknown_barcode.barcode)
                self.unknown_barcodes.append(unknown_barcode)
                return
            barcode_sequence: Optional[str] = node.attrib.get("name")
            if not barcode_sequence:
                self._skip_entry = True
                return
            if barcode_sequence.lower() == "all":
                self._skip_entry = True
                return

            self._skip_entry = False
            self.set_current_barcode(barcode=barcode_sequence)
        elif current_tag == "Project":
            self.set_project(project_name=node.attrib["name"])
        elif current_tag == "Flowcell":
            self.set_flowcell_id(node.attrib["flowcell-id"])
        elif current_tag == "TopUnknownBarcodes":
            LOG.debug("Set unknown barcodes entry to true")
            self._skip_entry = False
            self.unknown_barcodes_entry = True

    def evaluate_end_event(self, node: Element, current_tag: str) -> None:
        # We will add the information for each tile
        if "Tile" in self.current_path:
            self.process_tile_info(node=node, current_tag=current_tag)
        elif current_tag == "Lane":
            if self.unknown_barcodes_entry:
                self.create_unknown_barcodes_entry()
            else:
                self.create_entry()

    def update_cluster_count(self, cluster_count: int) -> None:
        if "Raw" in self.current_path:
            self._results.raw_cluster_count += cluster_count
        else:
            self._results.pass_filter_cluster_count += cluster_count

    def update_yield(self, yield_count: int) -> None:
        if "Raw" in self.current_path:
            self._results.raw_yield += yield_count
            return
        if "Read_1" in self.current_path:
            self._results.pass_filter_read1_yield += yield_count
        else:
            self._results.pass_filter_read2_yield += yield_count

    def update_quality_yield(self, yield_count: int) -> None:
        if "Raw" in self.current_path:
            # We don't case about quality yield for raw results
            return
        if "Read_1" in self.current_path:
            self._results.pass_filter_read1_q30 += yield_count
        else:
            self._results.pass_filter_read2_q30 += yield_count

    def update_quality_score_sum(self, quality_score: int) -> None:
        if "Raw" in self.current_path:
            # We don't case about quality score raw results
            return
        self._results.pass_filter_quality_score_sum += quality_score

    def process_tile_info(self, node: Element, current_tag: str) -> None:
        if current_tag == "ClusterCount":
            self.update_cluster_count(cluster_count=int(node.text))
        elif current_tag == "Yield":
            self.update_yield(yield_count=int(node.text))
        elif current_tag == "YieldQ30":
            self.update_quality_yield(yield_count=int(node.text))
        elif current_tag == "QualityScoreSum":
            self.update_quality_score_sum(quality_score=int(node.text))

    def set_current_lane(self, lane_nr: int) -> None:
        LOG.debug("Set current lane to %s", lane_nr)
        self._current_lane = lane_nr
        self.lanes.add(lane_nr)

    def set_current_barcode(self, barcode: str) -> None:
        LOG.debug("Set current barcode %s", barcode)
        self._current_barcode = barcode
        self.barcodes.add(barcode)
        self.barcode_to_sample[barcode] = self._current_sample

    def set_current_sample(self, sample_name: str) -> None:
        LOG.debug("Set current sample to %s", sample_name)
        self._current_sample = sample_name
        self.samples.add(sample_name)

    def set_project(self, project_name: str) -> None:
        LOG.debug("Set current project to %s", project_name)
        self.projects.add(project_name)

    def set_flowcell_id(self, flowcell: str) -> None:
        LOG.debug("Set flowcell id to %s", flowcell)
        self.flowcell_id = flowcell

    def __repr__(self):
        return f"ConversionStats(flowcell_id={self.flowcell_id},projects={self.projects},lanes={self.lanes}"
