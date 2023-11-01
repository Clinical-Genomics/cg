"""Module for reading and writing xml files."""
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from cg.constants import FileExtensions
from cg.exc import XMLError
from cg.io.validate_path import validate_file_suffix

LOG = logging.getLogger(__name__)


def read_xml(file_path: Path) -> ET.ElementTree:
    """Read content in a xml file to an ElementTree."""
    validate_file_suffix(path_to_validate=file_path, target_suffix=FileExtensions.XML)
    tree = ET.parse(file_path)
    return tree


def write_xml(tree: ET.ElementTree, file_path: Path) -> None:
    """Write content to a xml file."""
    tree.write(file_path, encoding="utf-8", xml_declaration=True)


def validate_node_exists(node: ET.Element | None, name: str) -> None:
    """Validates if the given node is not None.
    Raises:
        XMLError: If the node is None
    """
    if node is None:
        message = f"Could not determine {name}"
        LOG.warning(message)
        raise XMLError(message)
