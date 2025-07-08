from pathlib import Path
from unittest import mock

import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.services.analysis_starter.configurator.file_creators.nextflow.gene_panel import (
    GenePanelFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION],
)
def test_create_nextflow_configurator(
    workflow: Workflow,
    nextflow_case_id: str,
    nextflow_root: str,
    configurator_scenario: dict,
    mocker: MockerFixture,
):
    """Test creating the case config for all Nextflow pipelines."""

    # GIVEN a Nextflow configurator and an expected case config
    configurator, expected_case_config = configurator_scenario[workflow]

    # GIVEN that all expected files are mocked to exist
    mocker.patch.object(Path, "exists", return_value=True)

    # WHEN getting the case config
    case_config = configurator.get_config(case_id=nextflow_case_id)

    # THEN we should get back a case config
    assert case_config == expected_case_config


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION],
)
def test_create_nextflow_configurator_flags(
    workflow: Workflow,
    nextflow_case_id: str,
    nextflow_root: str,
    configurator_scenario: dict,
    mocker: MockerFixture,
):
    """Test that using flags when configuring a case overrides the case config default values."""

    # GIVEN a Nextflow configurator
    configurator, _ = configurator_scenario[workflow]

    # GIVEN that all expected files are mocked to exist
    mocker.patch.object(Path, "exists", return_value=True)

    # WHEN getting the case config overriding the revision
    case_config = configurator.get_config(case_id=nextflow_case_id, revision="overridden")

    # THEN we should get back a case config with updated value
    assert case_config.revision == "overridden"


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION],
)
def test_create_nextflow_configurator_none_flags(
    workflow: Workflow,
    nextflow_case_id: str,
    nextflow_root: str,
    configurator_scenario: dict,
    mocker: MockerFixture,
):
    """Test that setting a flag to None does not override configurator fields with None."""

    # GIVEN a Nextflow configurator
    configurator, _ = configurator_scenario[workflow]

    # GIVEN that all expected files are mocked to exist
    mocker.patch.object(Path, "exists", return_value=True)

    # WHEN getting the case config and overriding revision with None
    case_config = configurator.get_config(case_id=nextflow_case_id, revision=None)

    # THEN we should get back a case config without altering the revision
    assert case_config.revision is not None
