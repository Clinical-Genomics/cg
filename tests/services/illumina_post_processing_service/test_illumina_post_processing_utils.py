"""Test utils of the illumina post processing service."""

from pathlib import Path

from cg.services.illumina_post_processing_service.utils import (
    get_flow_cell_model_from_run_parameters,
)


def test_get_flow_cell_model_from_run_parameters_with_mode_node_name(
    novaseq_x_run_parameters_path: Path,
):
    # GIVEN a run parameters file from a NovaSeq X run

    # WHEN getting the flow cell model from the run parameters file
    flow_cell_model = get_flow_cell_model_from_run_parameters(novaseq_x_run_parameters_path)

    # THEN the flow cell model should be returned
    assert flow_cell_model == "10B"


def test_get_flow_cel_model_from_run_parameters_with_flow_cell_mode_node_name(
    run_paramters_with_flow_cell_mode_node_name: Path,
):
    # GIVEN a run parameters file with a FlowCellMode node

    # WHEN getting the flow cell model from the run parameters file
    flow_cell_model = get_flow_cell_model_from_run_parameters(
        run_paramters_with_flow_cell_mode_node_name
    )

    # THEN the flow cell model should be returned
    assert flow_cell_model == "S1"


def test_get_flow_cell_model_from_run_paramters_without_model(run_parameters_without_model: Path):
    # GIVEN a run parameters file without a model

    # WHEN getting the flow cell model from the run parameters file
    flow_cell_model = get_flow_cell_model_from_run_parameters(run_parameters_without_model)

    # THEN the flow cell model should be None
    assert flow_cell_model is None
