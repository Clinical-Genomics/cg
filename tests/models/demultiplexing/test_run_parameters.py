import logging
from pathlib import Path

import pytest
from cg.constants.demultiplexing import FlowCellType, UNKNOWN_REAGENT_KIT_VERSION
from cg.exc import FlowCellError
from cg.models.demultiplex.run_parameters import RunParameters


def test_get_flow_cell_type_hiseq_run_parameters(hiseq_run_parameters: Path):
    """Test that reading a hiseq run_parameters file assigns the correct flow cell type."""
    # GIVEN a RunParameters object created from a Hiseq run parameters file
    run_parameters = RunParameters(run_parameters_path=hiseq_run_parameters)

    # WHEN fetching the flow cell type

    # THEN the flow cell type is hiseq
    assert run_parameters.flow_cell_type == FlowCellType.HISEQ


def test_get_flow_cell_type_novaseq_run_parameters(novaseq_run_parameters: Path):
    """Test that reading a Novaseq run_parameters file assigns the correct flow cell type."""
    # GIVEN a RunParameters object created from a Novaseq run parameters file
    run_parameters = RunParameters(run_parameters_path=novaseq_run_parameters)

    # WHEN fetching the flow cell type

    # THEN assert that the flow cell type is novaseq
    assert run_parameters.flow_cell_type == FlowCellType.NOVASEQ


def test_get_unknown_type_run_parameters(unknown_run_parameters: Path, caplog):
    """Test that reading a run_parameters with unknown flow cell file raises an error."""
    caplog.set_level(logging.INFO)
    # GIVEN a RunParameters object created from a run parameters file with unknown flow cell
    run_parameters = RunParameters(run_parameters_path=unknown_run_parameters)

    # WHEN fetching the flow cell type
    with pytest.raises(FlowCellError):
        # THEN assert that an exception was raised since the flow cell type was unknown
        run_parameters.flow_cell_type

    assert "Unknown flow cell type" in caplog.text


def test_get_flow_cell_type_when_missing(run_parameters_missing_flowcell_type: Path, caplog):
    """Test that reading a run_parameters with missing flow cell file raises an error."""
    caplog.set_level(logging.INFO)
    # GIVEN a RunParameters object created from a run parameters file with missing flow cell
    run_parameters = RunParameters(run_parameters_path=run_parameters_missing_flowcell_type)

    # WHEN parsing the run parameters
    with pytest.raises(FlowCellError):
        # THEN assert that an exception was raised since the flow cell type was unknown
        run_parameters.flow_cell_type

    assert "Could not determine flow cell type" in caplog.text


def test_get_base_mask(novaseq_run_parameters: Path):
    """Test that generating the run parameters base mask returns the expected result."""
    # GIVEN a RunParameters object created from a valid run parameters file
    run_parameters = RunParameters(run_parameters_path=novaseq_run_parameters)

    # WHEN fetching the base mask
    base_mask: str = run_parameters.get_base_mask()

    # THEN the base mask has the correct structure
    assert base_mask.startswith("Y")
    assert ",I" in base_mask


def test_get_base_mask_undetermined_cycles(run_parameters_missing_flowcell_type: Path, caplog):
    """Test that generating the base mask from a file without cycle info fails."""
    caplog.set_level(logging.INFO)
    # GIVEN a RunParameters object created from a run parameters file with missing cycle info
    run_parameters = RunParameters(run_parameters_path=run_parameters_missing_flowcell_type)

    # WHEN creating the base mask
    with pytest.raises(FlowCellError):
        # THEN assert that an exception was raised since the cycle data was not found
        run_parameters.get_base_mask()

    assert "Could not determine length of reads one" in caplog.text


def test_flow_cell_mode(novaseq_run_parameters: Path):
    """Test that the flow cell mode is of a valid file in the list of expected values."""
    # GIVEN a RunParameters object created from a valid run parameters file
    run_parameters = RunParameters(run_parameters_path=novaseq_run_parameters)

    # WHEN fetching the flow cell mode

    # THEN the flow cell mode is in the list of expected values
    assert run_parameters.flow_cell_mode in ["S2", "S4"]


def test_flow_cell_mode_missing_mode(run_parameters_missing_flowcell_type: Path):
    """Test that getting the flow cell mode from a file lacking flow cell mode returns None."""
    # GIVEN a RunParameters object created from a file without flow cell mode
    run_parameters = RunParameters(run_parameters_path=run_parameters_missing_flowcell_type)

    # WHEN fetching the flow cell mode

    # THEN the flow cell mode is none
    assert run_parameters.flow_cell_mode is None


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
