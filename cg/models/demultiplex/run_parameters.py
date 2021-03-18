import logging
from pathlib import Path
from typing import Literal
from xml.etree import ElementTree

LOG = logging.getLogger(__name__)


class RunParameters:
    """Class to handle the run parameters from a sequencing run"""

    def __init__(self, run_parameters: Path):
        self.run_parameters: Path = run_parameters
        with open(run_parameters, "rt") as in_file:
            self.tree: ElementTree = ElementTree.parse(in_file)
        self.flowcell_type: str = self.get_flowcell_type()
        self.reagent_kit_version: str = self.get_reagent_kit_version()
        self.control_software_version: str = self.get_control_software_version()
        self.index_reads = self.get_index_reads()

    def get_index_reads(self) -> int:
        return 8

    def get_control_software_version(self) -> str:
        return "1.7.0"

    def get_reagent_kit_version(self) -> str:
        return "1"

    def get_flowcell_type(self) -> Literal["novaseq", "hiseq"]:
        """Fetch the flowcell type from the run parameters"""
        # First try with the node name for hiseq
        node_name = "./Setup/ApplicationName"
        xml_node = self.tree.find(node_name)
        if xml_node is None:
            # Then try with node name for novaseq
            node_name = ".Application"
            xml_node = self.tree.find(node_name)
        if xml_node is None:
            message = "Could not determine flowcell type"
            LOG.warning(message)
            raise SyntaxError(message)
        for flow_cell_name in ["novaseq", "hiseq"]:
            if flow_cell_name in xml_node.text.lower():
                return flow_cell_name
        message = f"Unknown flowcell type {xml_node.text}"
        LOG.warning(message)
        raise SyntaxError(message)

    def get_node_integer_value(self, node_name: str) -> int:
        xml_node = self.tree.find(node_name)
        return int(xml_node.text)

    def index_read_one(self) -> int:
        """Get the value for index read one"""
        node_name = "./IndexRead1NumberOfCycles"
        return self.get_node_integer_value(node_name)

    def index_read_two(self) -> int:
        """Get the value for index read one"""
        node_name = "./IndexRead2NumberOfCycles"
        return self.get_node_integer_value(node_name)

    def read_one_nr_cycles(self) -> int:
        """Get the nr of cycles for read one"""
        node_name = "./Read1NumberOfCycles"
        return self.get_node_integer_value(node_name)

    def read_two_nr_cycles(self) -> int:
        """Get the nr of cycles for read one"""
        node_name = "./Read2NumberOfCycles"
        return self.get_node_integer_value(node_name)

    def base_mask(self) -> str:
        """create the bcl2fastq basemask for novaseq flowcells

        Basemask is used in this comma format as an argument to bcl2fastq.
        When creating the unaligned path the commas are stripped
        """
        return (
            f"Y{self.read_one_nr_cycles()},"
            f"I{self.index_read_one()},"
            f"I{self.read_two_nr_cycles()},"
            f"Y{self.index_read_two()}"
        )
