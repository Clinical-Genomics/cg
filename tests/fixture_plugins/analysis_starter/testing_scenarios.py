import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file import (
    raredisease,
    rnafusion,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.rnafusion import (
    RNAFusionParamsFileCreator,
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


@pytest.fixture
def params_file_scenario(
    raredisease_params_file_creator: RarediseaseParamsFileCreator,
    expected_raredisease_params_file_content: dict,
    rnafusion_params_file_creator: RNAFusionParamsFileCreator,
    expected_rnafusion_params_file_content: dict,
    mocker: MockerFixture,
) -> dict:
    return {
        Workflow.RAREDISEASE: (
            raredisease_params_file_creator,
            expected_raredisease_params_file_content,
            mocker.patch.object(raredisease, "write_yaml_nextflow_style", return_value=None),
        ),
        Workflow.RNAFUSION: (
            rnafusion_params_file_creator,
            expected_rnafusion_params_file_content,
            mocker.patch.object(rnafusion, "write_yaml_nextflow_style", return_value=None),
        ),
    }


@pytest.fixture
def sample_sheet_scenario(
    raredisease_sample_sheet_creator: RarediseaseSampleSheetCreator,
    raredisease_sample_sheet_expected_content: list[list[str]],
    rnafusion_sample_sheet_creator: RNAFusionSampleSheetCreator,
    rnafusion_sample_sheet_expected_content: list[list[str]],
    taxprofiler_sample_sheet_creator: TaxprofilerSampleSheetCreator,
    taxprofiler_sample_sheet_expected_content: list[list[str]],
) -> dict:
    return {
        Workflow.RAREDISEASE: (
            raredisease_sample_sheet_creator,
            raredisease_sample_sheet_expected_content,
        ),
        Workflow.RNAFUSION: (
            rnafusion_sample_sheet_creator,
            rnafusion_sample_sheet_expected_content,
        ),
        Workflow.TAXPROFILER: (
            taxprofiler_sample_sheet_creator,
            taxprofiler_sample_sheet_expected_content,
        ),
    }


@pytest.fixture
def configurator_scenario(
    raredisease_configurator: NextflowConfigurator,
    raredisease_case_config: NextflowCaseConfig,
    rnafusion_configurator: NextflowConfigurator,
    rnafusion_case_config: NextflowCaseConfig,
) -> dict:
    return {
        Workflow.RAREDISEASE: (
            raredisease_configurator,
            raredisease_case_config,
        ),
        Workflow.RNAFUSION: (
            rnafusion_configurator,
            rnafusion_case_config,
        ),
    }
