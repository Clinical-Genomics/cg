import logging
from pathlib import Path

import pytest
from cg.models.demultiplex.run_parameters import RunParameters


def test_get_flowcell_type_hiseq_run_parameters(hiseq_run_parameters: Path):
    # GIVEN the path to a file with hiseq run parameters
    # GIVEN a RunParameters object
    run_parameters_object = RunParameters(hiseq_run_parameters)

    # WHEN fetching the flowcell type

    # THEN assert that the flowcell type is correct
    assert run_parameters_object.flowcell_type == "hiseq"


def test_get_flowcell_type_novaseq_run_parameters(novaseq_run_parameters: Path):
    # GIVEN the path to a file with hiseq run parameters
    # GIVEN a RunParameters object
    run_parameters_object = RunParameters(novaseq_run_parameters)

    # WHEN fetching the flowcell type

    # THEN assert that the flowcell type is correct
    assert run_parameters_object.flowcell_type == "novaseq"


def test_get_unknown_type_run_parameters(unknown_run_parameters: Path, caplog):
    caplog.set_level(logging.INFO)
    # GIVEN the path to a file with a unknown flowcell type

    # WHEN parsing the run parameters
    with pytest.raises(SyntaxError):
        # THEN assert that an exception was raised since the flowcell type was unknown
        RunParameters(unknown_run_parameters)

    assert "Unknown flowcell type" in caplog.text


def test_get_flowcell_type_when_missing(run_parameters_missing_flowcell_type: Path, caplog):
    caplog.set_level(logging.INFO)
    # GIVEN the path to a file where the field that indicates flowcell type is missing

    # WHEN parsing the run parameters
    with pytest.raises(SyntaxError):
        # THEN assert that an exception was raised since the flowcell type was unknown
        RunParameters(run_parameters_missing_flowcell_type)

    assert "Could not determine flowcell type" in caplog.text
