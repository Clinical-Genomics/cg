from pathlib import Path

from cg.models.demultiplex.demultiplex_data import RunParameters


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
