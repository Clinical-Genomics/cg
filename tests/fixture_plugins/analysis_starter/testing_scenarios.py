import pytest

from cg.constants import Workflow
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
    taxprofiler_configurator: NextflowConfigurator,
    taxprofiler_case_config: NextflowCaseConfig,
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
        Workflow.TAXPROFILER: (
            taxprofiler_configurator,
            taxprofiler_case_config,
        ),
    }
