"""Module for modeling run parameters file parsing."""
import logging
from pathlib import Path
from typing import Optional, Dict
from xml.etree import ElementTree

from cg.constants.demultiplexing import UNKNOWN_REAGENT_KIT_VERSION
from cg.constants.sequencing import Sequencers
from cg.exc import FlowCellError

LOG = logging.getLogger(__name__)


class RunParameters:
    """Base class with basic functions to handle the run parameters from a sequencing run."""

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

    @property
    def requires_dummy_samples(self) -> Optional[bool]:
        """Return true if the flow cell requires the addition of dummy samples."""
        raise NotImplementedError("Impossible to know dummy sample requirements of parent class")

    @property
    def control_software_version(self) -> Optional[str]:
        """Return the control software version if existent."""
        raise NotImplementedError(
            "Impossible to retrieve control software version from parent class"
        )

    @property
    def reagent_kit_version(self) -> Optional[str]:
        """Return the reagent kit version if existent."""
        raise NotImplementedError("Impossible to retrieve reagent kit version from parent class")

    @property
    def sequencer(self) -> Optional[str]:
        """Return the sequencer associated with the current run parameters."""
        raise NotImplementedError("Impossible to retrieve sequencer from parent class")

    def get_index1_cycles(self) -> int:
        """Return the number of cycles in the first index read."""
        raise NotImplementedError("Impossible to retrieve index1 cycles from parent class")

    def get_index2_cycles(self) -> int:
        """Return the number of cycles in the second index read."""
        raise NotImplementedError("Impossible to retrieve index2 cycles from parent class")

    def get_read1_cycles(self) -> int:
        """Return the number of cycles in the first read."""
        raise NotImplementedError("Impossible to retrieve read1 cycles from parent class")

    def get_read2_cycles(self) -> int:
        """Return the number of cycles in the second read."""
        raise NotImplementedError("Impossible to retrieve read2 cycles from parent class")

    def __str__(self):
        return f"RunParameters(path={self.path}," f"sequencer={self.sequencer})"

    def __repr__(self):
        return (
            f"RunParameters(path={self.path},"
            f"reagent_kit_version={self.reagent_kit_version},control_software_version={self.control_software_version},"
            f"index_length={self.index_length},"
            f"sequencer={self.sequencer})"
        )


class RunParametersNovaSeq6000(RunParameters):
    """Specific class for parsing run parameters of NovaSeq6000 sequencing."""

    @property
    def requires_dummy_samples(self) -> bool:
        """Return true if the number of cycles of both indexes is 8."""
        return self.index_length != 8

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
    def sequencer(self) -> str:
        """Return the sequencer associated with the current run parameters."""
        return Sequencers.NOVASEQ

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


class RunParametersNovaSeqX(RunParameters):
    """Specific class for parsing run parameters of NovaSeqX sequencing."""

    @property
    def requires_dummy_samples(self) -> bool:
        """Return False for run parameters associated with NovaSeqX sequencing."""
        return False

    @property
    def control_software_version(self) -> None:
        """Return None for run parameters associated with NovaSeqX sequencing."""
        return

    @property
    def reagent_kit_version(self) -> None:
        """Return None for run parameters associated with NovaSeqX sequencing."""
        return

    @property
    def sequencer(self) -> str:
        """Return the sequencer associated with the current run parameters."""
        return Sequencers.NOVASEQX

    @property
    def planned_reads(self) -> Dict[str, int]:
        """Return parsed read and index cycle values."""
        cycle_mapping: Dict[str, int] = {}
        for read_elem in self.tree.findall(".//Read"):
            read_name = read_elem.get("ReadName")
            cycles = self.get_node_integer_value(read_elem, "Cycles")
            cycle_mapping[read_name] = cycles
        return cycle_mapping

    def get_index1_cycles(self) -> int:
        """Return the number of cycles in the first index read."""
        return self.planned_reads.get("Index1")

    def get_index2_cycles(self) -> int:
        """Return the number of cycles in the second index read."""
        return self.planned_reads.get("Index2")

    def get_read1_cycles(self) -> int:
        """Return the number of cycles in the first read."""
        return self.planned_reads.get("Read1")

    def get_read2_cycles(self) -> int:
        """Return the number of cycles in the second read."""
        return self.planned_reads.get("Read2")
