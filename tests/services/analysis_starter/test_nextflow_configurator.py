from pathlib import Path
from typing import cast
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import SampleSheetCreator
from cg.constants import Workflow
from cg.constants.priority import SlurmQos
from cg.exc import MissingConfigFilesError
from cg.models.cg_config import (
    CommonAppConfig,
    NalloConfig,
    RarediseaseConfig,
    RnafusionConfig,
    TaxprofilerConfig,
)
from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)
from cg.services.analysis_starter.configurator.extensions.raredisease import RarediseaseExtension
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.nallo import (
    NalloParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.rnafusion import (
    RNAFusionParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.taxprofiler import (
    TaxprofilerParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.nallo import (
    NalloSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.raredisease import (
    RarediseaseSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion import (
    RNAFusionSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.taxprofiler import (
    TaxprofilerSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.store.models import Analysis, Case
from cg.store.store import Store


@pytest.mark.parametrize(
    "workflow",
    [Workflow.NALLO, Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER],
)
def test_get_config(
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

    # GIVEN a pipeline extension
    extension: PipelineExtension = create_autospec(PipelineExtension)
    configurator.pipeline_extension = extension

    # WHEN getting the case config
    case_config = configurator.get_config(case_id=nextflow_case_id)

    # THEN we should get back a case config
    assert case_config == expected_case_config

    # THEN the pipeline extension should have been called with ensure_required_files_exist
    cast(Mock, extension.do_required_files_exist).assert_called_once_with(
        case_run_directory=Path(nextflow_root, nextflow_case_id)
    )


def test_get_config_missing_required_files(mocker: MockerFixture):
    # GIVEN a nextflow configurator

    # GIVEN a raredisease config
    pipeline_config = create_autospec(
        RarediseaseConfig,
        root="/root",
        repository="https://repo.scilifelab.se",
        revision="rev123",
        profile="profile",
        pre_run_script="some_script.sh",
    )

    # GIVEN a store
    store_mock = create_autospec(Store)
    store_mock.get_case_workflow = Mock(return_value=Workflow.RAREDISEASE)
    store_mock.get_case_priority = Mock(return_value="normal")

    # GIVEN a several file creators
    sample_sheet_creator = create_autospec(RarediseaseSampleSheetCreator)
    params_file_creator = create_autospec(RarediseaseParamsFileCreator)
    config_file_creator = create_autospec(NextflowConfigFileCreator)

    # GIVEN a pipeline extension
    pipeline_extension = create_autospec(RarediseaseExtension)

    # GIVEN the extension indicates missing files
    pipeline_extension.do_required_files_exist = Mock(return_value=False)

    # GIVEN a nextflow configurator
    configurator = NextflowConfigurator(
        config_file_creator=config_file_creator,
        params_file_creator=params_file_creator,
        pipeline_config=pipeline_config,
        sample_sheet_creator=sample_sheet_creator,
        store=store_mock,
        pipeline_extension=pipeline_extension,
    )

    # GIVEN that the files created by the configurator are mocked to exist
    mocker.patch.object(Path, "exists", return_value=True)

    # WHEN calling get_config
    # THEN an exception is raised
    with pytest.raises(MissingConfigFilesError):
        configurator.get_config(case_id="case123")


@pytest.mark.parametrize(
    "workflow",
    [Workflow.NALLO, Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER],
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
    mocker.patch.object(
        configurator.pipeline_extension, "do_required_files_exist", return_value=True
    )

    # WHEN getting the case config overriding the revision
    case_config = configurator.get_config(case_id=nextflow_case_id, pre_run_script="overridden")

    # THEN we should get back a case config with updated value
    assert case_config.pre_run_script == "overridden"


def test_get_config_resume(
    nextflow_case_id: str, raredisease_configurator: NextflowConfigurator, mocker: MockerFixture
):
    # GIVEN a Nextflow Configurator with a case and a
    analysis: Analysis = create_autospec(Analysis, session_id="session_id")
    case: Case = create_autospec(Case, analyses=[analysis])
    raredisease_configurator.store.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN that all expected files are mocked to exist
    mocker.patch.object(Path, "exists", return_value=True)
    mocker.patch.object(
        raredisease_configurator.pipeline_extension, "do_required_files_exist", return_value=True
    )

    # WHEN calling get_config using resume=True
    case_config: NextflowCaseConfig = raredisease_configurator.get_config(
        case_id=nextflow_case_id, resume=True
    )

    # THEN the resume attribute is True and the session id is as expected
    assert case_config.resume is True
    assert case_config.session_id == "session_id"


@pytest.mark.parametrize(
    "workflow",
    [Workflow.NALLO, Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER],
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

    # GIVEN that all required files exist for the pipeline extension
    mocker.patch.object(
        configurator.pipeline_extension, "do_required_files_exist", return_value=True
    )

    # WHEN getting the case config and overriding pre-run-script with None
    case_config = configurator.get_config(case_id=nextflow_case_id, pre_run_script=None)

    # THEN we should get back a case config without altering the pre-run-script
    assert case_config.pre_run_script is not None


@pytest.mark.parametrize(
    "workflow, params_file_creator_class, pipeline_config_class, sample_sheet_creator_class",
    [
        (
            Workflow.NALLO,
            NalloParamsFileCreator,
            NalloConfig,
            NalloSampleSheetCreator,
        ),
        (
            Workflow.RAREDISEASE,
            RarediseaseParamsFileCreator,
            RarediseaseConfig,
            RarediseaseSampleSheetCreator,
        ),
        (
            Workflow.RNAFUSION,
            RNAFusionParamsFileCreator,
            RnafusionConfig,
            RNAFusionSampleSheetCreator,
        ),
        (
            Workflow.TAXPROFILER,
            TaxprofilerParamsFileCreator,
            TaxprofilerConfig,
            TaxprofilerSampleSheetCreator,
        ),
    ],
    ids=["Nallo", "raredisease", "RNAFUSION", "Taxprofiler"],
)
def test_configure(
    workflow: Workflow,
    params_file_creator_class: type[ParamsFileCreator],
    pipeline_config_class: type[CommonAppConfig],
    sample_sheet_creator_class: type[SampleSheetCreator],
    mocker: MockerFixture,
):
    # GIVEN a pipeline config
    pipeline_config = create_autospec(
        pipeline_config_class,
        root="/root",
        repository="https://repo.scilifelab.se",
        revision="rev123",
        profile="profile",
        pre_run_script="some_script.sh",
    )

    # GIVEN a store
    store_mock = create_autospec(Store)
    store_mock.get_case_workflow = Mock(return_value=workflow)
    store_mock.get_case_priority = Mock(return_value="normal")

    # GIVEN a several file creators
    sample_sheet_creator = create_autospec(sample_sheet_creator_class)
    params_file_creator = create_autospec(params_file_creator_class)
    config_file_creator = create_autospec(NextflowConfigFileCreator)

    # GIVEN a pipeline extension
    pipeline_extension = create_autospec(PipelineExtension)

    # GIVEN a nextflow configurator
    configurator = NextflowConfigurator(
        config_file_creator=config_file_creator,
        params_file_creator=params_file_creator,
        pipeline_config=pipeline_config,
        sample_sheet_creator=sample_sheet_creator,
        store=store_mock,
        pipeline_extension=pipeline_extension,
    )

    # GIVEN that the case run directory is correctly created
    mkdir_mock = mocker.patch.object(Path, "mkdir")

    # GIVEN that all expected files are mocked to exist
    mocker.patch.object(Path, "exists", return_value=True)

    # GIVEN a case ID
    case_id = "case123"

    # WHEN we configure the case
    config: NextflowCaseConfig = configurator.configure(case_id=case_id)

    # THEN the returned config should be as expected
    case_run_directory = Path("/root", case_id)
    expected_config = NextflowCaseConfig(
        case_id=case_id,
        workflow=workflow,
        case_priority=SlurmQos.NORMAL,
        config_profiles=["profile"],
        nextflow_config_file=Path(case_run_directory, f"{case_id}_nextflow_config.json").as_posix(),
        params_file=Path(case_run_directory, f"{case_id}_params_file.yaml").as_posix(),
        pipeline_repository="https://repo.scilifelab.se",
        pre_run_script="some_script.sh",
        revision="rev123",
        work_dir=Path(case_run_directory, "work").as_posix(),
    )
    assert config == expected_config

    # THEN the case run directory should have been created
    mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)

    # THEN the file creators should have been called
    sample_sheet_path = Path(case_run_directory, f"{case_id}_samplesheet.csv")
    sample_sheet_creator.create.assert_called_once_with(
        case_id=case_id, file_path=sample_sheet_path
    )
    params_file_creator.create.assert_called_once_with(
        case_id=case_id,
        file_path=Path(case_run_directory, f"{case_id}_params_file.yaml"),
        sample_sheet_path=sample_sheet_path,
    )
    config_file_creator.create.assert_called_once_with(
        case_id=case_id, file_path=Path(case_run_directory, f"{case_id}_nextflow_config.json")
    )

    # THEN the pipeline extension should have been configured
    pipeline_extension.configure.assert_called_once_with(
        case_id=case_id, case_run_directory=case_run_directory
    )
