import logging
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest

from cg.constants.demultiplexing import RunParametersXMLNodes
from cg.constants.sequencing import Sequencers
from cg.exc import RunParametersError, XMLError
from cg.models.demultiplex.run_parameters import (
    RunParameters,
    RunParametersHiSeq,
    RunParametersNovaSeq6000,
    RunParametersNovaSeqX,
)


@pytest.mark.parametrize(
    "run_parameters_path_fixture",
    [
        "hiseq_x_single_index_run_parameters_path",
        "hiseq_2500_double_index_run_parameters_path",
        "novaseq_6000_run_parameters_path",
        "novaseq_x_run_parameters_path",
    ],
)
def test_run_parameters_parent_class_fails(
    run_parameters_path_fixture: str, request: FixtureRequest
):
    """Test that trying to instantiate the parent RunParameters class raises an error."""
    # GIVEN a valid path for a run parameters file
    run_parameters_path: Path = request.getfixturevalue(run_parameters_path_fixture)

    # WHEN trying to instantiate the parent class with a RunParameters path
    with pytest.raises(NotImplementedError) as exc_info:
        # THEN an NotImplementedError is raised
        RunParameters(run_parameters_path=run_parameters_path)
    assert "Parent class instantiated" in str(exc_info)


def test_run_parameters_hiseq_x(hiseq_x_single_index_run_parameters_path: Path):
    """Tests that creating a HiSeq RunParameters with a HiSeqX path file works."""
    # GIVEN a valid HiSeqX run parameters file path

    # WHEN creating a HiSeqX RunParameters object
    run_parameters = RunParametersHiSeq(hiseq_x_single_index_run_parameters_path)

    # THEN the created object is of the correct type
    assert isinstance(run_parameters, RunParametersHiSeq)
    # THEN the sequencer is HiSeqX
    assert run_parameters.sequencer == Sequencers.HISEQX


def test_run_parameters_hiseq_2500(hiseq_2500_double_index_run_parameters_path: Path):
    """Tests that creating a HiSeq RunParameters with a HiSeq2500 path file works."""
    # GIVEN a valid HiSeq2500 run parameters file path

    # WHEN creating a HiSeq2500 RunParameters object
    run_parameters = RunParametersHiSeq(hiseq_2500_double_index_run_parameters_path)

    # THEN the created object is of the correct type
    assert isinstance(run_parameters, RunParametersHiSeq)
    # THEN the sequencer is HiSeq2500
    assert run_parameters.sequencer == Sequencers.HISEQGA


def test_run_parameters_hiseq_wrong_file(novaseq_6000_run_parameters_path: Path):
    """Tests that creating a RunParameters HiSeq object with the wrong file fails."""
    # GIVEN a file path with a run parameters file from an instrument different from HiSeq

    # WHEN trying to create a HiSeq RunParameters object with the file
    with pytest.raises(RunParametersError) as exc_info:
        # THEN a RunParametersError is raised
        RunParametersHiSeq(run_parameters_path=novaseq_6000_run_parameters_path)
    assert (
        f"Could not find node {RunParametersXMLNodes.APPLICATION_NAME} in the run parameters file"
        in str(exc_info.value)
    )


def test_run_parameters_novaseq_6000(novaseq_6000_run_parameters_path: Path):
    """Tests that creating a RunParameters NovaSeq6000 object with the correct file works."""
    # GIVEN a valid NovaSeq6000 run parameters file path

    # WHEN creating a NovaSeq6000 RunParameters object
    run_parameters = RunParametersNovaSeq6000(run_parameters_path=novaseq_6000_run_parameters_path)

    # THEN the created object is of the correct type and has the correct attributes
    assert isinstance(run_parameters, RunParametersNovaSeq6000)
    assert run_parameters.sequencer == Sequencers.NOVASEQ


def test_run_parameters_novaseq_6000_wrong_file(novaseq_x_run_parameters_path: Path):
    """Tests that creating a RunParameters NovaSeq6000 object with the wrong file fails."""
    # GIVEN a file path with a run parameters file from an instrument different from NovaSeq6000

    # WHEN trying to create a NovaSeq6000 RunParameters object with the file
    with pytest.raises(RunParametersError) as exc_info:
        # THEN a RunParametersError is raised
        RunParametersNovaSeq6000(run_parameters_path=novaseq_x_run_parameters_path)
    assert (
        str(exc_info.value)
        == f"The file parsed does not correspond to {RunParametersXMLNodes.NOVASEQ_6000_APPLICATION}"
    )


def test_run_parameters_novaseq_x(novaseq_x_run_parameters_path: Path):
    """Tests that creating a RunParameters NovaSeqX object with the correct file works."""
    # GIVEN a valid NovaSeqX run parameters file path

    # WHEN creating a NovaSeqX RunParameters object
    run_parameters = RunParametersNovaSeqX(run_parameters_path=novaseq_x_run_parameters_path)

    # THEN the created object is of the correct type and has the correct attributes
    assert isinstance(run_parameters, RunParametersNovaSeqX)
    assert run_parameters.sequencer == Sequencers.NOVASEQX


def test_run_parameters_novaseq_x_wrong_file(novaseq_6000_run_parameters_path: Path):
    """Tests that creating a RunParameters NovaSeqX object with the wrong file fails."""
    # GIVEN a file path with a run parameters file from an instrument different from NovaSeqX

    # WHEN trying to create a NovaSeqX RunParameters object with the file
    with pytest.raises(RunParametersError) as exc_info:
        # THEN a RunParametersError is raised
        RunParametersNovaSeqX(run_parameters_path=novaseq_6000_run_parameters_path)
    assert (
        f"Could not find node {RunParametersXMLNodes.INSTRUMENT_TYPE} in the run parameters"
        in str(exc_info.value)
    )


def test_run_parameters_novaseq_x_file_wrong_instrument(run_parameters_wrong_instrument: Path):
    """Test that initialising a NovaSeqX with a RunParameters file with a wrong instrument fails."""
    # GIVEN a RunParameters file with a wrong instrument

    # WHEN initialising the NovaSeqX
    with pytest.raises(RunParametersError) as exc_info:
        # THEN assert that an exception was raised since the control software version was not found
        RunParametersNovaSeqX(run_parameters_path=run_parameters_wrong_instrument)

    assert (
        str(exc_info.value)
        == f"The file parsed does not correspond to {RunParametersXMLNodes.NOVASEQ_X_INSTRUMENT}"
    )


@pytest.mark.parametrize(
    "run_parameters_fixture",
    [
        "hiseq_2500_run_parameters_double_index",
        "hiseq_x_run_parameters_single_index",
        "novaseq_x_run_parameters",
    ],
)
def test_reagent_kit_version_hiseq_and_novaseq_x(
    run_parameters_fixture: str, request: FixtureRequest
):
    """Test that getting reagent kit version from a HiSeq or NovaSeqX RunParameters returns None."""
    # GIVEN a valid RunParameters object
    run_parameters: RunParameters = request.getfixturevalue(run_parameters_fixture)

    # WHEN fetching the reagent kit version

    # THEN the reagent kit version is None
    assert not run_parameters.reagent_kit_version


def test_reagent_kit_version_novaseq_6000(novaseq_6000_run_parameters: RunParametersNovaSeq6000):
    """Test that getting reagent kit version from a correct file returns an expected value."""
    # GIVEN a valid RunParameters object for NovaSeq6000

    # WHEN fetching the reagent kit version
    reagent_kit_version: str = novaseq_6000_run_parameters.reagent_kit_version

    # THEN the reagent kit version exists and is not "unknown"
    assert reagent_kit_version
    assert reagent_kit_version != RunParametersXMLNodes.UNKNOWN_REAGENT_KIT_VERSION


def test_reagent_kit_version_novaseq_6000_missing_version(
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


@pytest.mark.parametrize(
    "run_parameters_fixture",
    [
        "hiseq_2500_run_parameters_double_index",
        "hiseq_x_run_parameters_single_index",
        "novaseq_x_run_parameters",
    ],
)
def test_control_software_version_hiseq_and_novaseq_x(
    run_parameters_fixture: str, request: FixtureRequest
):
    """Test that getting control software version from HiSeq/NovaSeqX RunParameters returns None."""
    # GIVEN a valid RunParameters object
    run_parameters: RunParameters = request.getfixturevalue(run_parameters_fixture)

    # WHEN fetching the control software version

    # THEN the control software version is None
    assert not run_parameters.control_software_version


def test_control_software_version_novaseq_6000(
    novaseq_6000_run_parameters: RunParametersNovaSeq6000,
):
    """Test that getting control software version from a correct file returns an expected value."""
    # GIVEN a valid RunParameters object for NovaSeq6000

    # WHEN fetching the control software version
    control_software_version: str = novaseq_6000_run_parameters.control_software_version

    # THEN the control software version is a non-empty string
    assert isinstance(control_software_version, str)
    assert control_software_version != ""


def test_control_software_version_novaseq_6000_no_version(
    run_parameters_missing_versions: Path, caplog
):
    """Test that fetching the control software version from a file without that field fails."""
    caplog.set_level(logging.INFO)
    # GIVEN a RunParameters object created from a file without control software version

    # WHEN fetching the control software version
    with pytest.raises(XMLError):
        # THEN assert that an exception was raised since the control software version was not found
        run_parameters_missing_versions.control_software_version

    assert (
        f"Could not find node with name {RunParametersXMLNodes.APPLICATION_VERSION} in XML tree"
        in caplog.text
    )


@pytest.mark.parametrize(
    "run_parameters_fixture, expected_index_length",
    [
        ("hiseq_2500_run_parameters_double_index", 8),
        ("hiseq_x_run_parameters_single_index", 8),
        ("novaseq_6000_run_parameters", 10),
        ("novaseq_x_run_parameters", 10),
    ],
)
def test_index_length(
    run_parameters_fixture: str, expected_index_length: int, request: FixtureRequest
):
    """Test getting the index length from RunParameters objects return expected values."""
    # GIVEN a valid RunParameters object
    run_parameters: RunParameters = request.getfixturevalue(run_parameters_fixture)

    # WHEN getting the index length
    real_index_length: int = run_parameters.index_length

    # THEN the index length is an int
    assert isinstance(real_index_length, int)
    # THEN the index length is the expected value
    assert real_index_length == expected_index_length


@pytest.mark.parametrize(
    "run_parameters_fixture",
    [
        "run_parameters_novaseq_6000_different_index",
        "run_parameters_novaseq_x_different_index",
    ],
)
def test_index_length_different_length(
    run_parameters_fixture: str,
    request: FixtureRequest,
):
    """Test that getting the index length from a file with different index cycles fails."""
    # GIVEN a NovaSeq6000 RunParameters object created from a file with different index cycles
    run_parameters: RunParameters = request.getfixturevalue(run_parameters_fixture)

    # WHEN fetching index length
    with pytest.raises(RunParametersError) as exc_info:
        # THEN assert that an exception was raised since the index cycles are different
        run_parameters.index_length
    assert str(exc_info.value) == "Index lengths are not the same!"


@pytest.mark.parametrize(
    "run_parameters_fixture",
    [
        "hiseq_2500_run_parameters_double_index",
        "hiseq_x_run_parameters_single_index",
        "novaseq_6000_run_parameters",
        "novaseq_x_run_parameters",
    ],
)
def test_get_cycles(run_parameters_fixture: str, request: FixtureRequest):
    """Test that the read and index cycles are read correctly for any RunParameters object."""
    # GIVEN a RunParameters object
    run_parameters: RunParameters = request.getfixturevalue(run_parameters_fixture)

    # WHEN getting any read cycle
    read_cycles: list[int] = [
        run_parameters.get_read_1_cycles(),
        run_parameters.get_read_2_cycles(),
        run_parameters.get_index_1_cycles(),
        run_parameters.get_index_2_cycles(),
    ]

    # THEN all read cycles are non-negative integers
    for cycles in read_cycles:
        assert isinstance(cycles, int)
        assert cycles >= 0
