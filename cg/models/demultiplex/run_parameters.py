"""Module for parsing sequencing run metadata from RunParameters file."""
import logging
from pathlib import Path
from xml.etree import ElementTree

from cg.constants.demultiplexing import RunParametersXMLNodes
from cg.constants.sequencing import Sequencers, sequencer_types
from cg.exc import RunParametersError
from cg.io.xml import read_xml, validate_node_exists

LOG = logging.getLogger(__name__)


class RunParameters:
    """Base class with basic functions to handle the run parameters from a sequencing run."""

    def __init__(self, run_parameters_path: Path):
        self.path: Path = run_parameters_path
        self.tree: ElementTree = read_xml(file_path=run_parameters_path)
        self.validate_instrument()

    def validate_instrument(self) -> None:
        """Raise an error if the parent class was instantiated."""
        raise NotImplementedError(
            "Parent class instantiated. Instantiate instead RunParametersHiSeq, "
            "RunParametersNovaSeq6000 or RunParametersNovaSeqX"
        )

    def is_single_index(self) -> bool:
        """Return False if the sequencing is not HiSeq. Overriden in HiSeq"""
        return False

    @property
    def index_length(self) -> int:
        """Return the length of the indexes if they are equal, raise an error otherwise."""
        index_one_length: int = self.get_index_1_cycles()
        index_two_length: int = self.get_index_2_cycles()
        if index_one_length != index_two_length and not self.is_single_index():
            raise RunParametersError("Index lengths are not the same!")
        return index_one_length

    def get_tree_node(self, node_name: str, name: str) -> ElementTree.Element:
        """Return the node of a tree given its name if it exists."""
        xml_node = self.tree.find(node_name)
        validate_node_exists(node=xml_node, name=name)
        return xml_node

    def get_node_string_value(self, node_name: str, name: str) -> str:
        """Return the value of the node as a string if its validation passes."""
        return self.get_tree_node(node_name=node_name, name=name).text

    def get_node_integer_value(self, node_name: str, name: str) -> int:
        """Return the value of the node as an integer if its validation passes."""
        return int(self.get_node_string_value(node_name=node_name, name=name))

    @property
    def control_software_version(self) -> str | None:
        """Return the control software version if existent."""
        raise NotImplementedError

    @property
    def reagent_kit_version(self) -> str | None:
        """Return the reagent kit version if existent."""
        raise NotImplementedError

    @property
    def sequencer(self) -> str | None:
        """Return the sequencer associated with the current run parameters."""
        raise NotImplementedError

    def get_index_1_cycles(self) -> int | None:
        """Return the number of cycles in the first index read."""
        raise NotImplementedError

    def get_index_2_cycles(self) -> int | None:
        """Return the number of cycles in the second index read."""
        raise NotImplementedError

    def get_read_1_cycles(self) -> int | None:
        """Return the number of cycles in the first read."""
        raise NotImplementedError

    def get_read_2_cycles(self) -> int | None:
        """Return the number of cycles in the second read."""
        raise NotImplementedError

    def __str__(self):
        return f"RunParameters(path={self.path}, sequencer={self.sequencer})"

    def __repr__(self):
        return (
            f"RunParameters(path={self.path},"
            f"reagent_kit_version={self.reagent_kit_version},"
            "control_software_version={self.control_software_version},"
            f"index_length={self.index_length},"
            f"sequencer={self.sequencer})"
        )


class RunParametersHiSeq(RunParameters):
    """Specific class for parsing run parameters of HiSeq2500 sequencing."""

    def validate_instrument(self) -> None:
        """Validate if a HiSeq file was used to instantiate the class.
        Raises:
            RunParametersError if the run parameters file is not HiSeq"""
        node_name: str = RunParametersXMLNodes.APPLICATION_NAME
        application: ElementTree.Element | None = self.tree.find(node_name)
        if application is None or application.text != RunParametersXMLNodes.HISEQ_APPLICATION:
            raise RunParametersError("The file parsed does not correspond to a HiSeq instrument")

    def is_single_index(self) -> bool:
        """Return whether the sequencing was done with a single index."""
        node_name: str = RunParametersXMLNodes.PLANNED_READS_HISEQ
        reads: ElementTree.Element = self.get_tree_node(node_name=node_name, name="Planned Reads")
        if self.get_index_2_cycles() == 0 and len(list(reads)) == 3:
            return True
        return False

    @property
    def control_software_version(self) -> None:
        """Return None for run parameters associated with HiSeq sequencing."""
        return

    @property
    def reagent_kit_version(self) -> None:
        """Return None for run parameters associated with HiSeq sequencing."""
        return

    @property
    def sequencer(self) -> str:
        """Return the sequencer associated with the current run parameters."""
        node_name: str = RunParametersXMLNodes.SEQUENCER_ID
        sequencer: str = self.get_node_string_value(node_name=node_name, name="Sequencer ID")
        return sequencer_types.get(sequencer)

    def get_index_1_cycles(self) -> int:
        """Return the number of cycles in the first index read."""
        node_name: str = RunParametersXMLNodes.INDEX_1_HISEQ
        return self.get_node_integer_value(node_name=node_name, name="length of index one")

    def get_index_2_cycles(self) -> int:
        """Return the number of cycles in the second index read."""
        node_name: str = RunParametersXMLNodes.INDEX_2_HISEQ
        return self.get_node_integer_value(node_name=node_name, name="length of index two")

    def get_read_1_cycles(self) -> int:
        """Return the number of cycles in the first read."""
        node_name: str = RunParametersXMLNodes.READ_1_HISEQ
        return self.get_node_integer_value(node_name=node_name, name="length of reads one")

    def get_read_2_cycles(self) -> int:
        """Return the number of cycles in the second read."""
        node_name: str = RunParametersXMLNodes.READ_2_HISEQ
        return self.get_node_integer_value(node_name=node_name, name="length of reads two")


class RunParametersNovaSeq6000(RunParameters):
    """Specific class for parsing run parameters of NovaSeq6000 sequencing."""

    def validate_instrument(self) -> None:
        """Validate if a NovaSeq6000 file was used to instantiate the class.
        Raises:
            RunParametersError if the run parameters file is not NovaSeq6000"""
        node_name: str = RunParametersXMLNodes.APPLICATION
        application: ElementTree.Element | None = self.tree.find(node_name)
        if (
            application is None
            or application.text != RunParametersXMLNodes.NOVASEQ_6000_APPLICATION
        ):
            raise RunParametersError(
                "The file parsed does not correspond to a NovaSeq6000 instrument"
            )

    @property
    def control_software_version(self) -> str:
        """Return the control software version."""
        node_name: str = RunParametersXMLNodes.APPLICATION_VERSION
        return self.get_node_string_value(node_name=node_name, name="control software version")

    @property
    def reagent_kit_version(self) -> str:
        """Return the reagent kit version if existent, return 'unknown' otherwise."""
        node_name: str = RunParametersXMLNodes.REAGENT_KIT_VERSION
        xml_node: ElementTree.Element | None = self.tree.find(node_name)
        if xml_node is None:
            LOG.warning("Could not determine reagent kit version")
            LOG.info("Set reagent kit version to 'unknown'")
            return RunParametersXMLNodes.UNKNOWN_REAGENT_KIT_VERSION
        return xml_node.text

    @property
    def sequencer(self) -> str:
        """Return the sequencer associated with the current run parameters."""
        return Sequencers.NOVASEQ

    def get_index_1_cycles(self) -> int:
        """Return the number of cycles in the first index read."""
        node_name: str = RunParametersXMLNodes.INDEX_1_NOVASEQ_6000
        return self.get_node_integer_value(node_name=node_name, name="length of index one")

    def get_index_2_cycles(self) -> int:
        """Return the number of cycles in the second index read."""
        node_name: str = RunParametersXMLNodes.INDEX_2_NOVASEQ_6000
        return self.get_node_integer_value(node_name=node_name, name="length of index two")

    def get_read_1_cycles(self) -> int:
        """Return the number of cycles in the first read."""
        node_name: str = RunParametersXMLNodes.READ_1_NOVASEQ_6000
        return self.get_node_integer_value(node_name=node_name, name="length of reads one")

    def get_read_2_cycles(self) -> int:
        """Return the number of cycles in the second read."""
        node_name: str = RunParametersXMLNodes.READ_2_NOVASEQ_6000
        return self.get_node_integer_value(node_name=node_name, name="length of reads two")


class RunParametersNovaSeqX(RunParameters):
    """Specific class for parsing run parameters of NovaSeqX sequencing."""

    def validate_instrument(self) -> None:
        """Validate if a NovaSeqX file was used to instantiate the class.
        Raises:
            RunParametersError if the run parameters file is not NovaSeqX"""
        node_name: str = RunParametersXMLNodes.INSTRUMENT_TYPE
        instrument: ElementTree.Element | None = self.tree.find(node_name)
        if instrument is None or instrument.text != RunParametersXMLNodes.NOVASEQ_X_INSTRUMENT:
            raise RunParametersError("The file parsed does not correspond to a NovaSeqX instrument")

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
    def read_parser(self) -> dict[str, int]:
        """Return read and index cycle values parsed as a dictionary."""
        cycle_mapping: dict[str, int] = {}
        planned_reads_tree: ElementTree.Element = self.get_tree_node(
            node_name=RunParametersXMLNodes.PLANNED_READS_NOVASEQ_X, name="Planned Reads"
        )
        planned_reads: list[ElementTree.Element] = planned_reads_tree.findall(
            RunParametersXMLNodes.INNER_READ
        )
        for read_elem in planned_reads:
            read_name: str = read_elem.get(RunParametersXMLNodes.READ_NAME)
            cycles: int = int(read_elem.get(RunParametersXMLNodes.CYCLES))
            cycle_mapping[read_name] = cycles
        return cycle_mapping

    def get_index_1_cycles(self) -> int:
        """Return the number of cycles in the first index read."""
        return self.read_parser.get(RunParametersXMLNodes.INDEX_1_NOVASEQ_X)

    def get_index_2_cycles(self) -> int:
        """Return the number of cycles in the second index read."""
        return self.read_parser.get(RunParametersXMLNodes.INDEX_2_NOVASEQ_X)

    def get_read_1_cycles(self) -> int:
        """Return the number of cycles in the first read."""
        return self.read_parser.get(RunParametersXMLNodes.READ_1_NOVASEQ_X)

    def get_read_2_cycles(self) -> int:
        """Return the number of cycles in the second read."""
        return self.read_parser.get(RunParametersXMLNodes.READ_2_NOVASEQ_X)
