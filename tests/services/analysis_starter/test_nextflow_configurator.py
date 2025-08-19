from pathlib import Path
from unittest.mock import create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.models.cg_config import RarediseaseConfig
from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.store.store import Store


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER],
)
def test_get_case_config(
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
    [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER],
)
def test_get_case_config_flags(
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
    case_config = configurator.get_config(case_id=nextflow_case_id, pre_run_script="overridden")

    # THEN we should get back a case config with updated value
    assert case_config.pre_run_script == "overridden"


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER],
)
def test_get_case_config_none_flags(
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

    # WHEN getting the case config and overriding pre-run-script with None
    case_config = configurator.get_config(case_id=nextflow_case_id, pre_run_script=None)

    # THEN we should get back a case config without altering the pre-run-script
    assert case_config.pre_run_script is not None


def test_raredisease_configure(mocker: MockerFixture):
    pipeline_config = create_autospec(
        RarediseaseConfig,
        root="/root",
        repository="http://repo.scilifelab.se",
        revision="rev123",
        profile="profile_raredisease",
        pre_run_script="some_script.sh",
    )

    configurator = NextflowConfigurator(
        config_file_creator=create_autospec(NextflowConfigFileCreator),
        params_file_creator=create_autospec(ParamsFileCreator),
        pipeline_config=pipeline_config,
        sample_sheet_creator=create_autospec(NextflowSampleSheetCreator),
        store=create_autospec(Store),
        pipeline_extension=create_autospec(PipelineExtension),
    )

    mocker.patch.object(Path, "mkdir")

    configurator.configure(case_id="case_id")
