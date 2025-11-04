import pytest

from cg.constants import Workflow
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig


@pytest.fixture
def configurator_scenario(
    nallo_configurator: NextflowConfigurator,
    nallo_case_config: NextflowCaseConfig,
    raredisease_configurator: NextflowConfigurator,
    raredisease_case_config: NextflowCaseConfig,
    rnafusion_configurator: NextflowConfigurator,
    rnafusion_case_config: NextflowCaseConfig,
    taxprofiler_configurator: NextflowConfigurator,
    taxprofiler_case_config: NextflowCaseConfig,
) -> dict:
    return {
        Workflow.NALLO: (
            nallo_configurator,
            nallo_case_config,
        ),
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
