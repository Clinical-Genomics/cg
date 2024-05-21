"""Fixtures for the tests of the IlluminaPostProcessingService."""

from pathlib import Path

import pytest


@pytest.fixture
def run_paramters_with_flow_cell_mode_node_name(fixtures_dir: Path) -> Path:
    return Path(
        fixtures_dir,
        "apps",
        "demultiplexing",
        "flow_cells",
        "230912_A00187_1009_AHK33MDRX3",
        "runParameters.xml",
    )


@pytest.fixture
def run_parameters_without_mode(fixtures_dir: Path) -> Path:
    return Path(
        fixtures_dir,
        "apps",
        "demultiplexing",
        "flow_cells",
        "170517_ST-E00266_0210_BHJCFFALXX",
        "runParameters.xml",
    )
