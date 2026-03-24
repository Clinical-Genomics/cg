"""Fixtures for the illumina demux version service."""

import json
from pathlib import Path

import pytest

from cg.services.illumina.file_parsing.demux_version_service import IlluminaDemuxVersionService


@pytest.fixture
def demux_version_file(novaseq_x_demux_runs_dir) -> Path:
    """Return the path to a demultiplexing log file."""
    return Path(
        novaseq_x_demux_runs_dir,
        "dragen-replay.json",
    )


@pytest.fixture
def highlevel_summary_file(tmp_path) -> Path:
    """Return the path to an on-instrument highlevel_summary.json file."""
    summary_dir = tmp_path / "summary" / "4.3.13"
    summary_dir.mkdir(parents=True)
    file_path = summary_dir / "highlevel_summary.json"
    file_path.write_text(
        json.dumps(
            {
                "run_id": "20250604_LH00188_0260_B232NWMLT3",
                "software_version": "4.3.13",
                "workflows": [
                    {
                        "workflow": "BCLConvert",
                        "num_samples_completed": 30,
                        "num_samples_failed": 0,
                        "num_samples_total": 30,
                    }
                ],
            }
        )
    )
    return file_path


@pytest.fixture
def illumina_demux_version_service() -> IlluminaDemuxVersionService:
    return IlluminaDemuxVersionService()


@pytest.fixture
def expected_demux_software_version() -> str:
    return "4.1.7"


@pytest.fixture
def expected_demux_software() -> str:
    return "dragen"
