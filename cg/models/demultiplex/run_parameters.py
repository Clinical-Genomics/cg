"""Module for parsing sequencing run metadata from RunParameters file."""

import logging
from abc import abstractmethod
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree

from packaging.version import parse

from cg.constants.demultiplexing import (
    NEW_NOVASEQ_CONTROL_SOFTWARE_VERSION,
    NEW_NOVASEQ_REAGENT_KIT_VERSION,
    NO_REVERSE_COMPLEMENTS_INDEX_SETTINGS,
    NOVASEQ_6000_POST_1_5_KITS_INDEX_SETTINGS,
    NOVASEQ_X_INDEX_SETTINGS,
    IndexSettings,
    RunParametersXMLNodes,
)
from cg.constants.sequencing import SEQUENCER_TYPES, Sequencers
from cg.exc import RunParametersError, XMLError
from cg.io.xml import get_tree_node, read_xml

LOG = logging.getLogger(__name__)


class RunParameters:
    """Base class with basic functions to handle the run parameters from a sequencing run."""

    def __init__(self, run_parameters_path: Path):
        self.path: Path = run_parameters_path
        self.tree: ElementTree = read_xml(file_path=run_parameters_path)
        self.validate_instrument()
        self.index_settings: IndexSettings = self._get_index_settings()

    def validate_instrument(self) -> None:
        """Raise an error if the parent class was instantiated."""
        raise NotImplementedError(
            "Parent class instantiated. Instantiate instead RunParametersHiSeq, "
            "RunParametersNovaSeq6000 or RunParametersNovaSeqX"
        )

    def _validate_instrument(self, node_name: str, node_value: str):
        """Fetches the node from an XML file and compares it with the expected value.
        Raises:
            RunParametersError if the node does not have the expected value."""
        try:
            application: Element | None = get_tree_node(tree=self.tree, node_name=node_name)
        except XMLError:
            raise RunParametersError(
                f"Could not find node {node_name} in the run parameters file. "
                "Check that the correct run parameters file is used"
            )
        if application.text != node_value:
            raise RunParametersError(f"The file parsed does not correspond to {node_value}")

    def _get_node_string_value(self, node_name: str) -> str:
        """Return the value of the node as a string if its validation passes."""
        return get_tree_node(tree=self.tree, node_name=node_name).text

    def _get_node_integer_value(self, node_name: str) -> int:
        """Return the value of the node as an integer if its validation passes."""
        return int(self._get_node_string_value(node_name=node_name))

    @property
    @abstractmethod
    def control_software_version(self) -> str | None:
        """Return the control software version if existent."""
        pass

    @property
    @abstractmethod
    def reagent_kit_version(self) -> str | None:
        """Return the reagent kit version if existent."""
        pass

    @property
    @abstractmethod
    def sequencer(self) -> str | None:
        """Return the sequencer associated with the current run parameters."""
        pass

    @abstractmethod
    def get_index_1_cycles(self) -> int | None:
        """Return the number of cycles in the first index read."""
        pass

    @abstractmethod
    def get_index_2_cycles(self) -> int | None:
        """Return the number of cycles in the second index read."""
        pass

    @abstractmethod
    def get_read_1_cycles(self) -> int | None:
        """Return the number of cycles in the first read."""
        pass

    @abstractmethod
    def get_read_2_cycles(self) -> int | None:
        """Return the number of cycles in the second read."""
        pass

    @property
    def is_single_index(self) -> bool:
        """Returns true if the sequencing run is single-index."""
        return self.get_index_2_cycles() == 0

    def _is_novaseq6000_post_1_5_kit(self) -> bool:
        """
        Returns whether sequencing was performed after the 1.5 consumables kits were introduced.
        This is indicated by the software version and the reagent kit fields in the run parameters.
        """
        if self.sequencer != Sequencers.NOVASEQ:
            return False
        if parse(self.control_software_version) < parse(NEW_NOVASEQ_CONTROL_SOFTWARE_VERSION):
            return False
        if parse(self.reagent_kit_version) < parse(NEW_NOVASEQ_REAGENT_KIT_VERSION):
            return False
        return True

    def _get_index_settings(self) -> IndexSettings:
        """Returns the correct index-related settings for the run in question."""
        if self.sequencer == Sequencers.NOVASEQX:
            LOG.debug("Using NovaSeqX index settings")
            return NOVASEQ_X_INDEX_SETTINGS
        if self._is_novaseq6000_post_1_5_kit():
            LOG.debug("Using NovaSeq 6000 post 1.5 kits index settings")
            return NOVASEQ_6000_POST_1_5_KITS_INDEX_SETTINGS
        return NO_REVERSE_COMPLEMENTS_INDEX_SETTINGS

    @abstractmethod
    def get_flow_cell_model(self):
        pass

    def __str__(self):
        return f"RunParameters(path={self.path}, sequencer={self.sequencer})"

    def __repr__(self):
        return (
            f"RunParameters(path={self.path},"
            f"reagent_kit_version={self.reagent_kit_version},"
            f"control_software_version={self.control_software_version},"
            f"index_lengths={self.get_index_1_cycles()}-{self.get_index_2_cycles()},"
            f"sequencer={self.sequencer})"
        )


class RunParametersHiSeq(RunParameters):
    """Specific class for parsing run parameters of HiSeq2500 sequencing."""

    def validate_instrument(self) -> None:
        """Validate if a HiSeq file was used to instantiate the class."""
        self._validate_instrument(
            node_name=RunParametersXMLNodes.APPLICATION_NAME,
            node_value=RunParametersXMLNodes.HISEQ_APPLICATION,
        )

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
        sequencer: str = self._get_node_string_value(node_name=node_name)
        return SEQUENCER_TYPES.get(sequencer)

    def get_index_1_cycles(self) -> int:
        """Return the number of cycles in the first index read."""
        node_name: str = RunParametersXMLNodes.INDEX_1_HISEQ
        return self._get_node_integer_value(node_name=node_name)

    def get_index_2_cycles(self) -> int:
        """Return the number of cycles in the second index read."""
        node_name: str = RunParametersXMLNodes.INDEX_2_HISEQ
        return self._get_node_integer_value(node_name=node_name)

    def get_read_1_cycles(self) -> int:
        """Return the number of cycles in the first read."""
        node_name: str = RunParametersXMLNodes.READ_1_HISEQ
        return self._get_node_integer_value(node_name=node_name)

    def get_read_2_cycles(self) -> int:
        """Return the number of cycles in the second read."""
        node_name: str = RunParametersXMLNodes.READ_2_HISEQ
        return self._get_node_integer_value(node_name=node_name)

    def get_flow_cell_model(self) -> None:
        """Return None for run parameters associated with HiSeq sequencing."""
        return None


class RunParametersNovaSeq6000(RunParameters):
    """Specific class for parsing run parameters of NovaSeq6000 sequencing."""

    def validate_instrument(self) -> None:
        """Validate if a NovaSeq6000 file was used to instantiate the class."""
        self._validate_instrument(
            node_name=RunParametersXMLNodes.APPLICATION,
            node_value=RunParametersXMLNodes.NOVASEQ_6000_APPLICATION,
        )

    @property
    def control_software_version(self) -> str:
        """Return the control software version."""
        node_name: str = RunParametersXMLNodes.APPLICATION_VERSION
        return self._get_node_string_value(node_name=node_name)

    @property
    def reagent_kit_version(self) -> str:
        """Return the reagent kit version if existent, return 'unknown' otherwise."""
        node_name: str = RunParametersXMLNodes.REAGENT_KIT_VERSION
        xml_node: Element | None = self.tree.find(node_name)
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
        return self._get_node_integer_value(node_name=node_name)

    def get_index_2_cycles(self) -> int:
        """Return the number of cycles in the second index read."""
        node_name: str = RunParametersXMLNodes.INDEX_2_NOVASEQ_6000
        return self._get_node_integer_value(node_name=node_name)

    def get_read_1_cycles(self) -> int:
        """Return the number of cycles in the first read."""
        node_name: str = RunParametersXMLNodes.READ_1_NOVASEQ_6000
        return self._get_node_integer_value(node_name=node_name)

    def get_read_2_cycles(self) -> int:
        """Return the number of cycles in the second read."""
        node_name: str = RunParametersXMLNodes.READ_2_NOVASEQ_6000
        return self._get_node_integer_value(node_name=node_name)

    def get_flow_cell_model(self) -> str:
        """Return the flow cell model referred to as 'FlowCellMode' in the run parameters file."""
        node_name: str = RunParametersXMLNodes.FLOW_CELL_MODE
        return self._get_node_string_value(node_name=node_name)


class RunParametersNovaSeqX(RunParameters):
    """Specific class for parsing run parameters of NovaSeqX sequencing."""

    def validate_instrument(self) -> None:
        """Validate if a NovaSeqX file was used to instantiate the class."""
        self._validate_instrument(
            node_name=RunParametersXMLNodes.INSTRUMENT_TYPE,
            node_value=RunParametersXMLNodes.NOVASEQ_X_INSTRUMENT,
        )

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
    def _read_parser(self) -> dict[str, int]:
        """Return read and index cycle values parsed as a dictionary."""
        cycle_mapping: dict[str, int] = {}
        planned_reads_tree: Element = get_tree_node(
            tree=self.tree, node_name=RunParametersXMLNodes.PLANNED_READS_NOVASEQ_X
        )
        planned_reads: list[Element] = planned_reads_tree.findall(RunParametersXMLNodes.INNER_READ)
        for read_elem in planned_reads:
            read_name: str = read_elem.get(RunParametersXMLNodes.READ_NAME)
            cycles: int = int(read_elem.get(RunParametersXMLNodes.CYCLES))
            cycle_mapping[read_name] = cycles
        return cycle_mapping

    def get_index_1_cycles(self) -> int:
        """Return the number of cycles in the first index read."""
        return self._read_parser.get(RunParametersXMLNodes.INDEX_1_NOVASEQ_X)

    def get_index_2_cycles(self) -> int:
        """Return the number of cycles in the second index read."""
        return self._read_parser.get(RunParametersXMLNodes.INDEX_2_NOVASEQ_X)

    def get_read_1_cycles(self) -> int:
        """Return the number of cycles in the first read."""
        return self._read_parser.get(RunParametersXMLNodes.READ_1_NOVASEQ_X)

    def get_read_2_cycles(self) -> int:
        """Return the number of cycles in the second read."""
        return self._read_parser.get(RunParametersXMLNodes.READ_2_NOVASEQ_X)

    def get_flow_cell_model(self) -> str:
        """Return the flow cell model referred to as 'Mode' or 'Name' in the run parameters file."""
        consumable_infos: list[Element] = self.tree.findall(".//ConsumableInfo")
        for consumable_info in consumable_infos:
            type_element: Element | None = consumable_info.find("Type")
            if type_element is not None and type_element.text == "FlowCell":
                name_element: Element | None = consumable_info.find("Name") or consumable_info.find(
                    "Mode"
                )
                if name_element is not None:
                    return name_element.text
