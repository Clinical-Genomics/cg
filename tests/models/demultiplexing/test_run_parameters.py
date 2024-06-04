import logging
from pathlib import Path
from typing import Type

import pytest
from _pytest.fixtures import FixtureRequest
from pydantic import BaseModel

from cg.constants.demultiplexing import (
    NO_REVERSE_COMPLEMENTS_INDEX_SETTINGS,
    NOVASEQ_6000_POST_1_5_KITS_INDEX_SETTINGS,
    NOVASEQ_X_INDEX_SETTINGS,
    IndexSettings,
    RunParametersXMLNodes,
)
from cg.constants.sequencing import Sequencers
from cg.exc import RunParametersError, XMLError
from cg.models.demultiplex.run_parameters import (
    RunParameters,
    RunParametersHiSeq,
    RunParametersNovaSeq6000,
    RunParametersNovaSeqX,
)
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData


@pytest.mark.parametrize(
    "run_parameters_path_fixture",
    [
        "hiseq_x_single_index_run_parameters_path",
        "hiseq_2500_dual_index_run_parameters_path",
        "novaseq_6000_run_parameters_pre_1_5_kits_path",
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


@pytest.mark.parametrize(
    "run_parameters_path, constructor, sequencer",
    [
        ("hiseq_x_single_index_run_parameters_path", RunParametersHiSeq, Sequencers.HISEQX),
        (
            "hiseq_2500_dual_index_run_parameters_path",
            RunParametersHiSeq,
            Sequencers.HISEQGA,
        ),
        (
            "novaseq_6000_run_parameters_pre_1_5_kits_path",
            RunParametersNovaSeq6000,
            Sequencers.NOVASEQ,
        ),
        ("novaseq_x_run_parameters_path", RunParametersNovaSeqX, Sequencers.NOVASEQX),
    ],
)
def test_run_parameters_init(
    run_parameters_path: str,
    constructor: Type[RunParameters],
    sequencer: str,
    request: FixtureRequest,
):
    """Test that the RunParameters class is instantiated correctly."""
    # GIVEN a valid path for a run parameters file
    run_parameters_path: Path = request.getfixturevalue(run_parameters_path)

    # WHEN initialising the correct RunParameters class
    run_parameters: RunParameters = constructor(run_parameters_path=run_parameters_path)

    # THEN the object is instantiated correctly and is of the correct type
    assert isinstance(run_parameters, constructor)
    # THEN the sequencer is correct
    assert run_parameters.sequencer == sequencer


class RunParametersScenario(BaseModel):
    wrong_run_parameters_path_fixture: str
    constructor: Type[RunParameters]
    error_msg: str


@pytest.mark.parametrize(
    "scenario",
    [
        RunParametersScenario(
            wrong_run_parameters_path_fixture="novaseq_6000_run_parameters_pre_1_5_kits_path",
            constructor=RunParametersHiSeq,
            error_msg=f"Could not find node {RunParametersXMLNodes.APPLICATION_NAME} in the run parameters file.",
        ),
        RunParametersScenario(
            wrong_run_parameters_path_fixture="novaseq_x_run_parameters_path",
            constructor=RunParametersHiSeq,
            error_msg=f"Could not find node {RunParametersXMLNodes.APPLICATION_NAME} in the run parameters file.",
        ),
        RunParametersScenario(
            wrong_run_parameters_path_fixture="novaseq_x_run_parameters_path",
            constructor=RunParametersNovaSeq6000,
            error_msg=f"The file parsed does not correspond to {RunParametersXMLNodes.NOVASEQ_6000_APPLICATION}",
        ),
        RunParametersScenario(
            wrong_run_parameters_path_fixture="hiseq_x_single_index_run_parameters_path",
            constructor=RunParametersNovaSeq6000,
            error_msg=f"Could not find node {RunParametersXMLNodes.APPLICATION} in the run parameters file.",
        ),
        RunParametersScenario(
            wrong_run_parameters_path_fixture="hiseq_x_single_index_run_parameters_path",
            constructor=RunParametersNovaSeqX,
            error_msg=f"Could not find node {RunParametersXMLNodes.INSTRUMENT_TYPE} in the run parameters file.",
        ),
        RunParametersScenario(
            wrong_run_parameters_path_fixture="novaseq_6000_run_parameters_pre_1_5_kits_path",
            constructor=RunParametersNovaSeqX,
            error_msg=f"Could not find node {RunParametersXMLNodes.INSTRUMENT_TYPE} in the run parameters file.",
        ),
    ],
    ids=[
        "NovaSeq 6000 file, HiSeq constructor",
        "NovaSeq X file, HiSeq constructor",
        "NovaSeq X file, NovaSeq6000 constructor",
        "HiSeq X file, NovaSeq600 constructor",
        "HiSeq X file, NovaSeqX constructor",
        "NovaSeq6000 constructor, NovaSeqX constructor",
    ],
)
def test_run_parameters_wrong_file(scenario: RunParametersScenario, request: FixtureRequest):
    """Test that creating a RunParameters object with a wrong file fails."""
    # GIVEN a run parameters path from an instrument different from the expected
    wrong_run_parameters_path: Path = request.getfixturevalue(
        scenario.wrong_run_parameters_path_fixture
    )

    # WHEN trying to create a RunParameters object with the file
    with pytest.raises(RunParametersError) as exc_info:
        # THEN a RunParametersError is raised
        scenario.constructor(run_parameters_path=wrong_run_parameters_path)
    assert scenario.error_msg in str(exc_info.value)


@pytest.mark.parametrize(
    "run_parameters_fixture",
    [
        "hiseq_2500_dual_index_run_parameters",
        "hiseq_x_single_index_run_parameters",
        "novaseq_x_run_parameters",
    ],
    ids=["HiSeq 2500 dual index", "HiSeq X single index", "NovaSeq X"],
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


def test_reagent_kit_version_novaseq_6000_post_1_5_kits(
    novaseq_6000_run_parameters_post_1_5_kits: RunParametersNovaSeq6000,
):
    """
    Test that getting reagent kit version from a NovaSeq6000 post 1.5 kits does not return unknown.
    """
    # GIVEN a valid RunParameters object for NovaSeq6000

    # WHEN fetching the reagent kit version
    reagent_kit_version: str = novaseq_6000_run_parameters_post_1_5_kits.reagent_kit_version

    # THEN the reagent kit version exists and is not "unknown"
    assert reagent_kit_version
    assert reagent_kit_version != RunParametersXMLNodes.UNKNOWN_REAGENT_KIT_VERSION


@pytest.mark.parametrize(
    "run_parameters_fixture",
    [
        "hiseq_2500_dual_index_run_parameters",
        "hiseq_x_single_index_run_parameters",
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
    novaseq_6000_run_parameters_pre_1_5_kits: RunParametersNovaSeq6000,
):
    """Test that getting control software version from a correct file returns an expected value."""
    # GIVEN a valid RunParameters object for NovaSeq6000

    # WHEN fetching the control software version
    control_software_version: str = (
        novaseq_6000_run_parameters_pre_1_5_kits.control_software_version
    )

    # THEN the control software version is a non-empty string
    assert isinstance(control_software_version, str)
    assert control_software_version != ""


def test_novaseq_6000_no_version(run_parameters_missing_versions_path: Path, caplog):
    """Test that creating a Run Parameters object from a file without version fails."""
    caplog.set_level(logging.INFO)
    # GIVEN the path of a RunParameters file without control software version

    # WHEN instantiating the object
    with pytest.raises(XMLError):
        # THEN assert that an exception was raised since the control software version was not found
        RunParametersNovaSeq6000(run_parameters_missing_versions_path)

    assert (
        f"Could not find node with name {RunParametersXMLNodes.APPLICATION_VERSION} in XML tree"
        in caplog.text
    )


@pytest.mark.parametrize(
    "run_parameters_fixture",
    [
        "hiseq_x_single_index_run_parameters",
        "hiseq_2500_dual_index_run_parameters",
        "novaseq_6000_run_parameters_pre_1_5_kits",
        "novaseq_6000_run_parameters_post_1_5_kits",
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


@pytest.mark.parametrize(
    "flow_cell_fixture, expected_result",
    [
        ("novaseq_6000_pre_1_5_kits_flow_cell", False),
        ("novaseq_6000_post_1_5_kits_flow_cell", True),
    ],
)
def test_is_novaseq6000_post_1_5_kit(
    flow_cell_fixture: str, expected_result: bool, request: FixtureRequest
):
    """Test that the correct index settings are returned for each NovaSeq flow cell type."""
    # GIVEN run parameters from a flow cell
    flow_cell: IlluminaRunDirectoryData = request.getfixturevalue(flow_cell_fixture)
    # WHEN checking if the flow cell was sequenced after the NovaSeq 6000 1.5 kits
    result: bool = flow_cell.run_parameters._is_novaseq6000_post_1_5_kit()
    # THEN the correct index settings are returned
    assert result == expected_result


@pytest.mark.parametrize(
    "sequencing_run, correct_settings",
    [
        ("novaseq_6000_pre_1_5_kits_flow_cell", NO_REVERSE_COMPLEMENTS_INDEX_SETTINGS),
        ("novaseq_6000_post_1_5_kits_flow_cell", NOVASEQ_6000_POST_1_5_KITS_INDEX_SETTINGS),
        ("novaseq_x_flow_cell", NOVASEQ_X_INDEX_SETTINGS),
    ],
)
def test_get_index_settings(
    correct_settings: IndexSettings,
    sequencing_run: str,
    request: FixtureRequest,
):
    """Test that the correct index settings are returned for each NovaSeq flow cell type."""
    # GIVEN run parameters for a flow cell
    sequencing_run: IlluminaRunDirectoryData = request.getfixturevalue(sequencing_run)
    # WHEN getting the index settings
    settings: IndexSettings = sequencing_run.run_parameters.index_settings
    # THEN the correct index settings are returned
    assert settings == correct_settings


@pytest.mark.parametrize(
    "run_parameters_fixture, expected_result",
    [
        ("hiseq_x_single_index_run_parameters", None),
        ("hiseq_2500_dual_index_run_parameters", None),
        ("novaseq_6000_run_parameters_pre_1_5_kits", "S4"),
        ("novaseq_6000_run_parameters_post_1_5_kits", "S1"),
        ("novaseq_x_run_parameters", "10B"),
    ],
)
def test_get_flow_cell_mode(
    run_parameters_fixture: str, expected_result: str | None, request: FixtureRequest
):
    """Test that the correct flow cell mode is returned for each RunParameters object."""
    # GIVEN a RunParameters object
    run_parameters: RunParameters = request.getfixturevalue(run_parameters_fixture)
    # WHEN getting the flow cell mode
    result: str | None = run_parameters.get_flow_cell_model()
    # THEN the correct flow cell mode is returned
    assert result == expected_result
