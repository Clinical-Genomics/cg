"""Module for reading and writing xml files."""

import xml.etree.ElementTree as ET

from cg.constants import FileExtensions
from cg.io.validate_path import validate_file_suffix
from pathlib import Path


def read_xml(file_path: Path) -> ET.ElementTree:
    """Read content in a xml file to an ElementTree."""
    validate_file_suffix(path_to_validate=file_path, target_suffix=FileExtensions.XML)
    tree = ET.parse(file_path)
    return tree


def write_xml(tree: ET.ElementTree, file_path: Path) -> None:
    """Write content to a xml file."""
    tree.write(file_path, encoding="utf-8", xml_declaration=True)
