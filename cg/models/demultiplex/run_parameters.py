import logging
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree

from cg.exc import FlowcellError
from typing_extensions import Literal

LOG = logging.getLogger(__name__)


class RunParameters:
    """Class to handle the run parameters from a sequencing run"""

    def __init__(self, run_parameters_path: Path):
        self.path: Path = run_parameters_path
        with open(run_parameters_path, "rt") as in_file:
            self.tree: ElementTree = ElementTree.parse(in_file)

    @property
    def index_length(self) -> int:
        index_one_length: int = self.index_read_one()
        index_two_length: int = self.index_read_two()
        if index_one_length != index_two_length:
            raise FlowcellError("Index lengths are not the same!")
        return index_one_length

    @property
    def control_software_version(self) -> str:
        node_name = ".ApplicationVersion"
        xml_node: Optional[ElementTree.Element] = self.tree.find(node_name)
        self.node_not_found(node=xml_node, name="control software version")
        return xml_node.text

    @property
    def reagent_kit_version(self) -> str:
        node_name = "./RfidsInfo/SbsConsumableVersion"
        xml_node: Optional[ElementTree.Element] = self.tree.find(node_name)
        if xml_node is None:
            LOG.warning("Could not determine reagent kit version")
            LOG.info("Set reagent kit version to 'unknown'")
            return "unknown"
        return xml_node.text

    @property
    def flowcell_type(self) -> Literal["novaseq", "hiseq"]:
        """Fetch the flowcell type from the run parameters"""
        # First try with the node name for hiseq
        node_name = "./Setup/ApplicationName"
        xml_node = self.tree.find(node_name)
        if xml_node is None:
            # Then try with node name for novaseq
            node_name = ".Application"
            xml_node = self.tree.find(node_name)
        self.node_not_found(node=xml_node, name="flowcell type")
        for flow_cell_name in ["novaseq", "hiseq"]:
            if flow_cell_name in xml_node.text.lower():
                return flow_cell_name
        message = f"Unknown flowcell type {xml_node.text}"
        LOG.warning(message)
        raise FlowcellError(message)

    @property
    def run_type(self) -> Literal["wgs", "fluffy"]:
        """Fetch what type of run the parameters is"""
        if self.index_length == 8:
            return "fluffy"
        return "wgs"

    @staticmethod
    def node_not_found(node: Optional[ElementTree.Element], name: str) -> None:
        """Raise exception if node if not found"""
        if node is None:
            message = f"Could not determine {name}"
            LOG.warning(message)
            raise FlowcellError(message)

    def get_node_integer_value(self, node_name: str, name: str) -> int:
        xml_node = self.tree.find(node_name)
        self.node_not_found(node=xml_node, name=name)
        return int(xml_node.text)

    def index_read_one(self) -> int:
        """Get the value for index read one"""
        node_name = "./IndexRead1NumberOfCycles"
        return self.get_node_integer_value(node_name=node_name, name="length of index one")

    def index_read_two(self) -> int:
        """Get the value for index read one"""
        node_name = "./IndexRead2NumberOfCycles"
        return self.get_node_integer_value(node_name=node_name, name="length of index two")

    def read_one_nr_cycles(self) -> int:
        """Get the nr of cycles for read one"""
        node_name = "./Read1NumberOfCycles"
        return self.get_node_integer_value(node_name=node_name, name="length of reads one")

    def read_two_nr_cycles(self) -> int:
        """Get the nr of cycles for read one"""
        node_name = "./Read2NumberOfCycles"
        return self.get_node_integer_value(node_name=node_name, name="length of reads two")

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

    def __str__(self):
        return f"RunParameters(path={self.path},flowcell_type={self.flowcell_type},run_type={self.run_type}"

    def __repr__(self):
        return (
            f"RunParameters(path={self.path},flowcell_type={self.flowcell_type},run_type={self.run_type},"
            f"reagent_kit_version={self.reagent_kit_version},control_software_version={self.control_software_version},"
            f"index_length={self.index_length})"
        )
