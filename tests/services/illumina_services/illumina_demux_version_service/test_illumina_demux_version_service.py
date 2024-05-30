"""Tests for the illumina demux version service."""

from pathlib import Path

from cg.services.illumina_services.illumina_metrics_service.illumina_demux_version_service import (
    IlluminaDemuxVersionService,
)


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
