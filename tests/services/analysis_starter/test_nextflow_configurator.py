from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.constants.priority import SlurmQos
from cg.models.cg_config import RarediseaseConfig
from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
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


@pytest.mark.parametrize(
    "workflow",
    [
        Workflow.RAREDISEASE,
    ],
    # Workflow.RNAFUSION, Workflow.TAXPROFILER], ""
)
def test_raredisease_configure(workflow: Workflow, mocker: MockerFixture):
    pipeline_config = create_autospec(
        RarediseaseConfig,
        root="/root",
        repository="https://repo.scilifelab.se",
        revision="rev123",
        profile="profile_raredisease",
        pre_run_script="some_script.sh",
    )

    store_mock = create_autospec(Store)
    store_mock.get_case_workflow = Mock(return_value="raredisease")
    store_mock.get_case_priority = Mock(return_value="normal")
    sample_sheet_creator = create_autospec(NextflowSampleSheetCreator)
    case_id = "case123"
    case_path = Path("/root", case_id)
    params_file_creator = create_autospec(RarediseaseParamsFileCreator)

    sample_sheet_path_mock = Path("/root", case_id, f"{case_id}_samplesheet.csv")
    # sample_sheet_creator.get_file_path.return_value = sample_sheet_path_mock

    config_file_creator = create_autospec(NextflowConfigFileCreator)

    pipeline_extension = create_autospec(PipelineExtension)

    configurator = NextflowConfigurator(
        config_file_creator=config_file_creator,
        params_file_creator=params_file_creator,
        pipeline_config=pipeline_config,
        sample_sheet_creator=sample_sheet_creator,
        store=store_mock,
        pipeline_extension=pipeline_extension,
    )

    mkdir_mock = mocker.patch.object(Path, "mkdir")

    # GIVEN that all expected files are mocked to exist
    mocker.patch.object(Path, "exists", return_value=True)

    config: NextflowCaseConfig = configurator.configure(case_id=case_id)

    expected_config = NextflowCaseConfig(
        case_id=case_id,
        workflow=Workflow.RAREDISEASE,
        case_priority=SlurmQos.NORMAL,
        config_profiles=["profile_raredisease"],
        nextflow_config_file=Path("/root", case_id, f"{case_id}_nextflow_config.json").as_posix(),
        params_file=Path("/root", case_id, f"{case_id}_params_file.yaml").as_posix(),
        pipeline_repository="https://repo.scilifelab.se",
        pre_run_script="some_script.sh",
        revision="rev123",
        work_dir=Path("/root", case_id, "work").as_posix(),
    )
    assert config == expected_config
    mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
    sample_sheet_creator.create.assert_called_once_with(
        case_id=case_id, file_path=Path(case_path, f"{case_id}_samplesheet.csv")
    )
    params_file_creator.create.assert_called_once_with(
        case_id=case_id,
        file_path=Path(case_path, f"{case_id}_params_file.yaml"),
        sample_sheet_path=sample_sheet_path_mock,
    )
    config_file_creator.create.assert_called_once_with(
        case_id=case_id, file_path=Path(case_path, f"{case_id}_nextflow_config.json")
    )
    pipeline_extension.configure.assert_called_once_with(case_id=case_id, case_path=case_path)
