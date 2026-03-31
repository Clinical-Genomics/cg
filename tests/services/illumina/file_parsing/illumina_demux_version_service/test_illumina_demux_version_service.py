"""Tests for the illumina demux version service."""

from pathlib import Path

from cg.services.illumina.file_parsing.demux_version_service import IlluminaDemuxVersionService


def test_get_demux_software_version(
    demux_version_file: Path,
    illumina_demux_version_service: IlluminaDemuxVersionService,
    expected_demux_software_version: str,
):
    """Test to get the demultiplexing software version."""
    # GIVEN a path to a demultiplexing log file

    # WHEN getting the demultiplexing software version
    demux_software_version: str = illumina_demux_version_service.get_demux_software_version(
        demux_version_file
    )

    # THEN assert that the demultiplexing software version is correct
    assert demux_software_version == expected_demux_software_version


def test_get_demux_software(
    demux_version_file: Path,
    illumina_demux_version_service: IlluminaDemuxVersionService,
    expected_demux_software: str,
):
    """Test to get the demultiplexing software."""
    # GIVEN a path to a demultiplexing log file

    # WHEN getting the demultiplexing software
    demux_software: str = illumina_demux_version_service.get_demux_software(demux_version_file)

    # THEN assert that the demultiplexing software is correct
    assert demux_software == expected_demux_software


def test_get_demux_software_version_from_highlevel_summary(
    highlevel_summary_file: Path,
    illumina_demux_version_service: IlluminaDemuxVersionService,
):
    """Test that software version is parsed from highlevel_summary.json."""
    # GIVEN a path to a highlevel_summary.json file

    # WHEN getting the demultiplexing software version
    version: str = illumina_demux_version_service.get_demux_software_version(highlevel_summary_file)

    # THEN the version from the file is returned
    assert version == "4.3.13"


def test_get_demux_software_from_highlevel_summary(
    highlevel_summary_file: Path,
    illumina_demux_version_service: IlluminaDemuxVersionService,
):
    """Test that software name is parsed from highlevel_summary.json."""
    # GIVEN a path to a highlevel_summary.json file

    # WHEN getting the demultiplexing software
    software: str = illumina_demux_version_service.get_demux_software(highlevel_summary_file)

    # THEN the software is dragen
    assert software == "dragen"
