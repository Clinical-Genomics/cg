import logging
from pathlib import Path

import pytest
from cg.constants.demultiplexing import UNKNOWN_REAGENT_KIT_VERSION
from cg.exc import FlowCellError
from cg.models.demultiplex.run_parameters import RunParameters


def test_reagent_kit_version(novaseq_run_parameters: Path):
    """Test that getting reagent kit version from a correct file returns an expected value."""
    # GIVEN a RunParameters object created from a valid run parameters file
    run_parameters = RunParameters(run_parameters_path=novaseq_run_parameters)

    # WHEN fetching the reagent kit version
    reagent_kit_version: str = run_parameters.reagent_kit_version

    # THEN the reagent kit version exists and is not "unknown"
    assert reagent_kit_version
    assert reagent_kit_version != UNKNOWN_REAGENT_KIT_VERSION


def test_reagent_kit_version_missing_version(run_parameters_missing_flowcell_type: Path, caplog):
    """Test that 'unknown' will be returned if the run parameters file has no reagent kit method."""
    caplog.set_level(logging.INFO)
    # GIVEN a RunParameters object created from a file without reagent kit version
    run_parameters = RunParameters(run_parameters_path=run_parameters_missing_flowcell_type)

    # WHEN fetching the reagent kit version

    # THEN the reagent kit version is unknown
    assert run_parameters.reagent_kit_version == UNKNOWN_REAGENT_KIT_VERSION
    assert "Could not determine reagent kit version" in caplog.text


def test_control_software_version(novaseq_run_parameters: Path):
    """Test that getting control software version from a correct file returns an expected value."""
    # GIVEN a RunParameters object created from a valid run parameters file
    run_parameters = RunParameters(run_parameters_path=novaseq_run_parameters)

    # WHEN fetching the control software version

    # THEN the control software version is a string
    assert isinstance(run_parameters.control_software_version, str)


def test_control_software_version_no_version(run_parameters_missing_flowcell_type: Path, caplog):
    """Test that fetching the control software version from a file without that field fails."""
    caplog.set_level(logging.INFO)
    # GIVEN a RunParameters object created from a file without control software version
    run_parameters = RunParameters(run_parameters_path=run_parameters_missing_flowcell_type)

    # WHEN fetching the control software version
    with pytest.raises(FlowCellError):
        # THEN assert that an exception was raised since the control software version was not found
        run_parameters.control_software_version

    assert "Could not determine control software version" in caplog.text


def test_index_length(novaseq_run_parameters: Path):
    """Test that getting the index length from a valid file returns the expected output."""
    # GIVEN a RunParameters object created from a valid run parameters file
    run_parameters = RunParameters(run_parameters_path=novaseq_run_parameters)

    # WHEN getting the index length

    # THEN the index length is an int
    assert isinstance(run_parameters.index_length, int)


def test_index_length_different_length(run_parameters_different_index: Path):
    """Test that getting the index length from a file with different index cycles fails."""
    # GIVEN a RunParameters object created from a file with different index cycles
    run_parameters = RunParameters(run_parameters_path=run_parameters_different_index)

    # WHEN fetching index length
    with pytest.raises(FlowCellError) as exc_info:
        # THEN assert that an exception was raised since the index cycles are different
        run_parameters.index_length

    assert str(exc_info.value) == "Index lengths are not the same!"
