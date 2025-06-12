"""Fixtures for the illumina demux version service."""

from pathlib import Path

import pytest

from cg.services.illumina.file_parsing.demux_version_service import (
    IlluminaDemuxVersionService,
)


@pytest.fixture
def demux_version_file(novaseq_x_demux_runs_dir) -> Path:
    """Return the path to a demultiplexing log file."""
    return Path(
        novaseq_x_demux_runs_dir,
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
