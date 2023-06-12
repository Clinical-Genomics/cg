"""Tests for the demultiplex flow cell class."""
from pathlib import Path

import pytest
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


def test_get_run_parameters_when_non_existing(fixtures_dir: Path):
    # GIVEN a flowcell object with a directory without run parameters
    flowcell_path: Path = (
        fixtures_dir
        / "apps"
        / "demultiplexing"
        / "demultiplexed-runs"
        / "201203_A00689_0200_AHVKJCDRXX"
    )
    flow_cell = FlowCellDirectoryData(flow_cell_path=flowcell_path)
    assert flow_cell.run_parameters_path.exists() is False

    # WHEN fetching the run parameters object
    with pytest.raises(FileNotFoundError):
        # THEN assert that a FileNotFound error is raised
        flow_cell.run_parameters
