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


def read_xml_stream(stream: str) -> ET.Element:
    """Read xml formatted stream."""
    root = ET.fromstring(stream)
    return root


def write_xml(root: ET.Element, file_path: Path):
    """Write content to a xml file."""
    tree = ET.ElementTree(root)
    tree.write(file_path, encoding="utf-8", xml_declaration=True)


def write_xml_stream(root: ET.Element) -> str:
    """Write content to a xml stream."""
    xml_string = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_string.decode("utf-8")
