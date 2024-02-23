"""Module for reading and writing xml files."""

import logging
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, parse

from cg.constants import FileExtensions
from cg.exc import XMLError
from cg.io.validate_path import validate_file_suffix

LOG = logging.getLogger(__name__)


def read_xml(file_path: Path) -> ElementTree:
    """Read content in a xml file to an ElementTree."""
    validate_file_suffix(path_to_validate=file_path, target_suffix=FileExtensions.XML)
    tree = parse(file_path)
    return tree


def write_xml(tree: ElementTree, file_path: Path) -> None:
    """Write content to a xml file."""
    tree.write(file_path, encoding="utf-8", xml_declaration=True)


def validate_node_exists(node: Element | None, name: str) -> None:
    """Validates if the given node is not None.
    Raises:
        XMLError: If the node is None
    """
    if node is None:
        message = f"Could not find node with name {name} in XML tree"
        LOG.warning(message)
        raise XMLError(message)


def get_tree_node(tree: ElementTree, node_name: str) -> Element:
    """Return the node of a tree given its name if it exists."""
    xml_node: Element = tree.find(node_name)
    validate_node_exists(node=xml_node, name=node_name)
    return xml_node
