"""Tests for the demultiplex flowcell class"""
from pathlib import Path

import pytest
from cg.models.demultiplex.flowcell import Flowcell


def test_get_run_parameters_when_non_existing(fixtures_dir: Path):
    # GIVEN a flowcell object with a directory without run parameters
    flowcell_path: Path = (
        fixtures_dir
        / "apps"
        / "demultiplexing"
        / "demultiplexed-runs"
        / "201203_A00689_0200_AHVKJCDRXX"
    )
    flowcell = Flowcell(flowcell_path=flowcell_path)
    assert flowcell.run_parameters_path.exists() is False

    # WHEN fetching the run parameters object
    with pytest.raises(FileNotFoundError):
        # THEN assert that a FileNotFound error is raised
        flowcell.run_parameters_object
