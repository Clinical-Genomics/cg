import logging
from pathlib import Path
from typing import List

import pytest
from cg.constants.demultiplexing import RunParametersXMLNodes
from cg.constants.sequencing import Sequencers
from cg.exc import RunParametersError
from cg.models.demultiplex.run_parameters import (
    RunParameters,
    RunParametersNovaSeq6000,
    RunParametersNovaSeqX,
)


def test_run_parameters_parent_class_fails(
    novaseq_6000_run_parameters_path: Path,
    novaseq_x_run_parameters_path: Path,
):
    """Test that trying to instantiate the parent RunParameters class raises an error."""
    # GIVEN valid paths for run parameters files

    # WHEN trying to instantiate the parent class with a NovaSeq6000 file
    with pytest.raises(NotImplementedError) as exc_info:
        # THEN an NotImplementedError is raised
        RunParameters(run_parameters_path=novaseq_6000_run_parameters_path)
        assert (
            str(exc_info.value)
            == "Parent class instantiated. Please instantiate a child class instead"
        )

    # WHEN trying to instantiate the parent class with a NovaSeqX file
    with pytest.raises(NotImplementedError) as exc_info:
        # THEN an NotImplementedError is raised
        RunParameters(run_parameters_path=novaseq_x_run_parameters_path)
        assert (
            str(exc_info.value)
            == "Parent class instantiated. Please instantiate a child class instead"
        )


def test_run_parameters_novaseq_6000(novaseq_6000_run_parameters_path: Path):
    """Tests that creating a RunParameters NovaSeq6000 object with the correct file works."""

    # GIVEN a valid NovaSeq6000 run parameters file path

    # WHEN creating a NovaSeq6000 RunParameters object
    run_parameters = RunParametersNovaSeq6000(run_parameters_path=novaseq_6000_run_parameters_path)

    # THEN the created object is of the correct type and has the correct attributes
    assert isinstance(run_parameters, RunParametersNovaSeq6000)
    assert run_parameters.sequencer == Sequencers.NOVASEQ.value


def test_run_parameters_novaseq_6000_wrong_file(novaseq_x_run_parameters_path: Path):
    """Tests that creating a RunParameters NovaSeq6000 object with the wrong file fails."""
    # GIVEN a file path with a run parameters file from an instrument different from NovaSeq6000

    # WHEN trying to create a NovaSeq6000 RunParameters object with the file
    with pytest.raises(RunParametersError) as exc_info:
        # THEN an error is raised
        RunParametersNovaSeq6000(run_parameters_path=novaseq_x_run_parameters_path)
        assert (
            str(exc_info.value) == "The file parsed does not correspond to a NovaSeq6000 instrument"
        )


def test_run_parameters_novaseq_x(novaseq_x_run_parameters_path: Path):
    """Tests that creating a RunParameters NovaSeqX object with the correct file works."""

    # GIVEN a valid NovaSeqX run parameters file path

    # WHEN creating a NovaSeqX RunParameters object
    run_parameters = RunParametersNovaSeqX(run_parameters_path=novaseq_x_run_parameters_path)

    # THEN the created object is of the correct type and has the correct attributes
    assert isinstance(run_parameters, RunParametersNovaSeqX)
    assert run_parameters.sequencer == Sequencers.NOVASEQX.value


def test_run_parameters_novaseq_x_wrong_file(novaseq_6000_run_parameters_path: Path):
    """Tests that creating a RunParameters NovaSeqX object with the wrong file fails."""
    # GIVEN a file path with a run parameters file from an instrument different from NovaSeqX

    # WHEN trying to create a NovaSeqX RunParameters object with the file
    with pytest.raises(RunParametersError) as exc_info:
        # THEN an error is raised
        RunParametersNovaSeqX(run_parameters_path=novaseq_6000_run_parameters_path)
        assert str(exc_info.value) == "The file parsed does not correspond to a NovaSeqX instrument"


def test_reagent_kit_version(novaseq_6000_run_parameters: RunParametersNovaSeq6000):
    """Test that getting reagent kit version from a correct file returns an expected value."""
    # GIVEN a valid RunParameters object for NovaSeq6000

    # WHEN fetching the reagent kit version
    reagent_kit_version: str = novaseq_6000_run_parameters.reagent_kit_version

    # THEN the reagent kit version exists and is not "unknown"
    assert reagent_kit_version
    assert reagent_kit_version != RunParametersXMLNodes.UNKNOWN_REAGENT_KIT_VERSION


def test_reagent_kit_version_missing_version(
    run_parameters_missing_versions: RunParametersNovaSeq6000, caplog
):
    """Test that 'unknown' will be returned if the run parameters file has no reagent kit method."""
    caplog.set_level(logging.INFO)
    # GIVEN a RunParameters object for NovaSeq6000 created from a file without reagent kit version

    # WHEN fetching the reagent kit version
    reagent_kit: str = run_parameters_missing_versions.reagent_kit_version

    # THEN the reagent kit version is unknown
    assert reagent_kit == RunParametersXMLNodes.UNKNOWN_REAGENT_KIT_VERSION
    assert "Could not determine reagent kit version" in caplog.text


def test_reagent_kit_version_novaseq_x(novaseq_x_run_parameters: RunParametersNovaSeqX):
    """Test that getting reagent kit version from a NovaSeqX run parameters returns None."""
    # GIVEN a valid RunParameters object for NovaSeqX

    # WHEN fetching the reagent kit version

    # THEN the reagent kit version is None
    assert not novaseq_x_run_parameters.reagent_kit_version


def test_control_software_version(novaseq_6000_run_parameters: RunParametersNovaSeq6000):
    """Test that getting control software version from a correct file returns an expected value."""
    # GIVEN a valid RunParameters object for NovaSeq6000

    # WHEN fetching the control software version
    control_software_version: str = novaseq_6000_run_parameters.control_software_version

    # THEN the control software version is a non-empty string
    assert isinstance(control_software_version, str)
    assert control_software_version != ""


def test_control_software_version_no_version(run_parameters_missing_versions: Path, caplog):
    """Test that fetching the control software version from a file without that field fails."""
    caplog.set_level(logging.INFO)
    # GIVEN a RunParameters object created from a file without control software version

    # WHEN fetching the control software version
    with pytest.raises(RunParametersError):
        # THEN assert that an exception was raised since the control software version was not found
        run_parameters_missing_versions.control_software_version

    assert "Could not determine control software version" in caplog.text


def test_control_software_version_novaseq_x(novaseq_x_run_parameters: RunParametersNovaSeqX):
    """Test that getting control software version from a NovaSeqX run parameters returns None."""
    # GIVEN a valid RunParameters object for NovaSeqX

    # WHEN fetching the control software version

    # THEN the control software version is None
    assert not novaseq_x_run_parameters.control_software_version


def test_index_length_novaseq_6000(
    novaseq_6000_run_parameters: RunParametersNovaSeq6000,
):
    """Test that getting the index length from a NovaSeq6000 run parameters file returns an int."""
    # GIVEN a valid RunParametersNovaSeq6000 object

    # WHEN getting the index length

    # THEN the index length is an int
    assert isinstance(novaseq_6000_run_parameters.index_length, int)


def test_index_length_novaseq_x(
    novaseq_x_run_parameters: RunParametersNovaSeqX,
):
    """Test that getting the index length from a NovaSeqX run parameters file returns an int."""
    # GIVEN a valid RunParametersNovaSeqX object

    # WHEN getting the index length

    # THEN the index length is an int
    assert isinstance(novaseq_x_run_parameters.index_length, int)


def test_index_length_novaseq_6000_different_length(
    run_parameters_novaseq_6000_different_index_path: Path,
    run_parameters_novaseq_x_different_index_path: Path,
):
    """Test that getting the index length from a file with different index cycles fails."""
    # GIVEN a RunParameters object created from a file with different index cycles
    run_parameters_novaseq_6000 = RunParametersNovaSeq6000(
        run_parameters_path=run_parameters_novaseq_6000_different_index_path
    )

    # WHEN fetching index length
    with pytest.raises(RunParametersError) as exc_info:
        # THEN assert that an exception was raised since the index cycles are different
        run_parameters_novaseq_6000.index_length
        assert str(exc_info.value) == "Index lengths are not the same!"


def test_index_length_novaseq_x_different_length(
    run_parameters_novaseq_x_different_index_path: Path,
):
    """Test that getting the index length from a file with different index cycles fails."""
    # GIVEN a RunParameters object created from a file with different index cycles
    run_parameters_novaseq_x = RunParametersNovaSeqX(
        run_parameters_path=run_parameters_novaseq_x_different_index_path
    )
    # WHEN fetching index length
    with pytest.raises(RunParametersError) as exc_info:
        # THEN assert that an exception was raised since the index cycles are different
        run_parameters_novaseq_x.index_length
        assert str(exc_info.value) == "Index lengths are not the same!"


def test_get_cycles_novaseq_6000(novaseq_6000_run_parameters: RunParametersNovaSeq6000):
    """Test that the read and index cycles are read correctly for NovaSeqX run parameters."""
    # GIVEN a NovaSeq6000 run parameters object

    # WHEN getting any read cycle
    read_cycles: List[int] = [
        novaseq_6000_run_parameters.get_read_1_cycles(),
        novaseq_6000_run_parameters.get_read_2_cycles(),
        novaseq_6000_run_parameters.get_index_1_cycles(),
        novaseq_6000_run_parameters.get_index_2_cycles(),
    ]

    # THEN all read cycles are non-negative integers
    for cycles in read_cycles:
        assert isinstance(cycles, int)
        assert cycles >= 0


def test_get_cycles_novaseq_x(novaseq_x_run_parameters: RunParametersNovaSeqX):
    """Test that the read and index cycles are read correctly for NovaSeqX run parameters."""
    # GIVEN a NovaSeqX run parameters object

    # WHEN getting any read cycle
    read_cycles: List[int] = [
        novaseq_x_run_parameters.get_read_1_cycles(),
        novaseq_x_run_parameters.get_read_2_cycles(),
        novaseq_x_run_parameters.get_index_1_cycles(),
        novaseq_x_run_parameters.get_index_2_cycles(),
    ]

    # THEN all read cycles are non-negative integers
    for cycles in read_cycles:
        assert isinstance(cycles, int)
        assert cycles >= 0
