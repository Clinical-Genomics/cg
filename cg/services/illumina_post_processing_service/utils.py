"""Utility functions for the Illumina post-processing service."""

from pathlib import Path
from xml.etree.ElementTree import ElementTree, Element

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles, RunParametersXMLNodes
from cg.exc import XMLError
from cg.io.xml import read_xml, get_tree_node


def create_delivery_file_in_flow_cell_directory(flow_cell_directory: Path) -> None:
    Path(flow_cell_directory, DemultiplexingDirsAndFiles.DELIVERY).touch()


def get_flow_cell_model_from_run_parameters(run_parameters_path: Path) -> str | None:
    """Return the model of the flow cell."""
    xml_tree: ElementTree = read_xml(run_parameters_path)
    node: Element | None = None
    for node_name in [RunParametersXMLNodes.MODE, RunParametersXMLNodes.FLOW_CELL_MODE]:
        try:
            node: Element = get_tree_node(xml_tree, node_name)
            return node.text
        except XMLError:
            continue
    return node
