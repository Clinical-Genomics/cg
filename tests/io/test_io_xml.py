"""Tests for the io.xml module."""
from cg.io.xml import read_xml, write_xml
import xml.etree.ElementTree as ET


def test_get_content_from_file(xml_file_path):
    """Tests read XML."""
    # GIVEN a xml file

    # WHEN reading the xml file
    raw_xml_content = read_xml(file_path=xml_file_path)

    # Then assert a list is returned
    assert isinstance(raw_xml_content, ET.ElementTree)


def test_write_xml(xml_file_path, xml_temp_path):
    """Tests write XML."""
    # GIVEN a xml file

    # GIVEN a file path to write to
    # WHEN reading the xml file
    raw_xml_content = read_xml(file_path=xml_file_path)

    # WHEN writing the xml file from dict
    write_xml(tree=raw_xml_content, file_path=xml_temp_path)
