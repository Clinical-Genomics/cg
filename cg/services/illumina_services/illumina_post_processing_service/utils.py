"""Utility functions for the Illumina post-processing service."""

from pathlib import Path
from xml.etree.ElementTree import ElementTree, Element

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles, RunParametersXMLNodes
from cg.exc import XMLError
from cg.io.xml import read_xml, get_tree_node


def create_delivery_file_in_flow_cell_directory(flow_cell_directory: Path) -> None:
    Path(flow_cell_directory, DemultiplexingDirsAndFiles.DELIVERY).touch()
