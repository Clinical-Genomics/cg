import logging
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree

from cg.constants.demultiplexing import FlowCellType, UNKNOWN_REAGENT_KIT_VERSION
from cg.exc import FlowCellError
from typing_extensions import Literal

LOG = logging.getLogger(__name__)


class RunParameters:
    """Class to handle the run parameters from a sequencing run."""

    def __init__(self, run_parameters_path: Path):
        self.path: Path = run_parameters_path
        with open(run_parameters_path, "rt") as in_file:
            self.tree: ElementTree = ElementTree.parse(in_file)

    @property
    def index_length(self) -> int:
        """Return the length of the indexes if they are equal, raise an error otherwise."""
        index_one_length: int = self.get_index1_cycles()
        index_two_length: int = self.get_index2_cycles()
        if index_one_length != index_two_length:
            raise FlowCellError("Index lengths are not the same!")
        return index_one_length

    @property
    def control_software_version(self) -> str:
        """Return the control software version."""
        node_name: str = ".ApplicationVersion"
        xml_node: Optional[ElementTree.Element] = self.tree.find(node_name)
        self.node_not_found(node=xml_node, name="control software version")
        return xml_node.text

    @property
    def reagent_kit_version(self) -> str:
        """Return the reagent kit version if existent, return 'unknown' otherwise."""
        node_name: str = "./RfidsInfo/SbsConsumableVersion"
        xml_node: Optional[ElementTree.Element] = self.tree.find(node_name)
        if xml_node is None:
            LOG.warning("Could not determine reagent kit version")
            LOG.info("Set reagent kit version to 'unknown'")
            return UNKNOWN_REAGENT_KIT_VERSION
        return xml_node.text

    @property
    def flow_cell_type(self) -> Literal[FlowCellType.NOVASEQ, FlowCellType.HISEQ]:
        """Fetch the flow cell type from the run parameters."""
        # First try with the node name for hiseq
        node_name: str = "./Setup/ApplicationName"
        xml_node: Optional[ElementTree.Element] = self.tree.find(node_name)
        if xml_node is None:
            # Then try with node name for novaseq
            node_name: str = ".Application"
            xml_node: Optional[ElementTree.Element] = self.tree.find(node_name)
        self.node_not_found(node=xml_node, name="flow cell type")
        for flow_cell_name in [FlowCellType.NOVASEQ, FlowCellType.HISEQ]:
            if flow_cell_name in xml_node.text.lower():
                return flow_cell_name
        message = f"Unknown flow cell type {xml_node.text}"
        LOG.warning(message)
        raise FlowCellError(message)

    @property
    def flow_cell_mode(self) -> Optional[str]:
        """Return the flow cell mode."""
        node_name: str = "/RfidsInfo/FlowCellMode"
        xml_node: Optional[ElementTree.Element] = self.tree.find(node_name)
        if xml_node is None:
            LOG.warning("Could not determine flow cell mode")
            LOG.info("Set flow cell mode to None")
            return
        return xml_node.text

    @property
    def requires_dummy_samples(self) -> bool:
        """Return true if the flow cell requires the addition of dummy samples.

        If the number of cycles of both indexes is 8, the flow cell does not need the addition of dummy samples.
        """
        return self.index_length != 8

    @staticmethod
    def node_not_found(node: Optional[ElementTree.Element], name: str) -> None:
        """Raise exception if the given node is not found."""
        if node is None:
            message = f"Could not determine {name}"
            LOG.warning(message)
            raise FlowCellError(message)

    def get_node_integer_value(self, node_name: str, name: str) -> int:
        """Return the value of the node as an integer."""
        xml_node = self.tree.find(node_name)
        self.node_not_found(node=xml_node, name=name)
        return int(xml_node.text)

    def get_index1_cycles(self) -> int:
        """Return the number of cycles in the first index read."""
        node_name = "./IndexRead1NumberOfCycles"
        return self.get_node_integer_value(node_name=node_name, name="length of index one")

    def get_index2_cycles(self) -> int:
        """Return the number of cycles in the second index read."""
        node_name = "./IndexRead2NumberOfCycles"
        return self.get_node_integer_value(node_name=node_name, name="length of index two")

    def get_read1_cycles(self) -> int:
        """Return the number of cycles in the first read."""
        node_name = "./Read1NumberOfCycles"
        return self.get_node_integer_value(node_name=node_name, name="length of reads one")

    def get_read2_cycles(self) -> int:
        """Return the number of cycles in the second read."""
        node_name = "./Read2NumberOfCycles"
        return self.get_node_integer_value(node_name=node_name, name="length of reads two")

    def get_base_mask(self) -> str:
        """Create the basemask for novaseq flow cells.

        Basemask is used in this comma format as an argument to bcl2fastq.
        When creating the unaligned path the commas are stripped.
        """
        return (
            f"Y{self.get_read1_cycles()},"
            f"I{self.get_index1_cycles()},"
            f"I{self.get_index2_cycles()},"
            f"Y{self.get_read2_cycles()}"
        )

    def __str__(self):
        return (
            f"RunParameters(path={self.path},"
            f"flow_cell_type={self.flow_cell_type},"
            f"flow_cell_mode={self.flow_cell_mode})"
        )

    def __repr__(self):
        return (
            f"RunParameters(path={self.path},flow_cell_type={self.flow_cell_type},flow_cell_mode={self.flow_cell_mode},"
            f"reagent_kit_version={self.reagent_kit_version},control_software_version={self.control_software_version},"
            f"index_length={self.index_length})"
        )
