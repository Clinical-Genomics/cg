from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION],
)
def test_create_rnafusion_configurator(
    workflow: Workflow,
    nextflow_case_id: str,
    nextflow_root: str,
    configurator_scenario: dict,
    mocker: MockerFixture,
):
    """Test creating the case config for all pipelines."""

    # GIVEN a Nextflow configurator and an expected case config
    configurator, expected_case_config = configurator_scenario[workflow]

    # GIVEN that IO operations are mocked
    mocker.patch.object(Path, "exists", return_value=True)

    # GIVEN that the case path is mocked
    configurator.root_dir = nextflow_root

    # WHEN getting the case config
    case_config = configurator.get_config(case_id=nextflow_case_id)

    # THEN we should get back a case config
    assert case_config == expected_case_config


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION],
)
def test_create_rnafusion_configurator_flags(
    workflow: Workflow,
    nextflow_case_id: str,
    nextflow_root: str,
    configurator_scenario: dict,
    mocker: MockerFixture,
):
    """Test that using flags when configuring a case overrides the case config default values."""
    # GIVEN a Nextflow configurator and an expected case config
    configurator, _ = configurator_scenario[workflow]

    # GIVEN that IO operations are mocked
    mocker.patch.object(Path, "exists", return_value=True)

    # GIVEN that the case path is mocked
    configurator.root_dir = nextflow_root

    # WHEN getting the case config
    case_config = configurator.get_config(case_id=nextflow_case_id, revision="overridden")

    # THEN we should get back a case config with updated value
    assert case_config.revision == "overridden"
