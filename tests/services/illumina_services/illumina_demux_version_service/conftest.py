"""Fixtures for the illumina demux version service."""

from pathlib import Path

import pytest

from cg.services.illumina_services.illumina_metrics_service.illumina_demux_version_service import (
    IlluminaDemuxVersionService,
)


@pytest.fixture
def demux_version_file() -> Path:
    """Return the path to a demultiplexing log file."""
    return Path(
        "tests",
        "fixtures",
        "apps",
        "demultiplexing",
        "demultiplexed-runs",
        "20231108_LH00188_0028_B22F52TLT3",
        "dragen-replay.json",
    )


@pytest.fixture
def illumina_demux_version_service() -> IlluminaDemuxVersionService:
    return IlluminaDemuxVersionService()


@pytest.fixture
def expected_demux_software_version() -> str:
    return "4.1.7"


@pytest.fixture
def expected_demux_software() -> str:
    return "dragen"
