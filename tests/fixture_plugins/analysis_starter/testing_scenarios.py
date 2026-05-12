from collections.abc import Callable
from typing import NamedTuple

import pytest
from mock import create_autospec

from cg.constants import Workflow
from cg.models.cg_config import (
    CommonAppConfig,
    NalloConfig,
    RarediseaseConfig,
    RnafusionConfig,
    TaxprofilerConfig,
    TomteConfig,
)
from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)
from cg.services.analysis_starter.configurator.extensions.tomte_extension import TomteExtension
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.nallo import (
    NalloParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease_params_file_creator import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.rnafusion import (
    RNAFusionParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.taxprofiler import (
    TaxprofilerParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.tomte_params_file_creator import (
    TomteParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.nallo_sample_sheet_creator import (
    NalloSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.protocol import (
    SampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.raredisease_sample_sheet_creator import (
    RarediseaseSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion_sample_sheet_creator import (
    RNAFusionSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.taxprofiler_sample_sheet_creator import (
    TaxprofilerSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.tomte_sample_sheet_creator import (
    TomteSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig


class AnalysisStarterScenario(NamedTuple):
    nextflow_config: type[CommonAppConfig]
    params_file_creator: type[ParamsFileCreator]
    pipeline_extension: type[PipelineExtension]
    sample_sheet_creator: type[SampleSheetCreator]
    store: str


@pytest.fixture
def configurator_scenario(
    request: pytest.FixtureRequest,
    get_nextflow_case_config_dict: Callable,
    get_nextflow_config_dict: Callable,
) -> Callable[[Workflow], tuple[NextflowConfigurator, NextflowCaseConfig]]:

    scenarios: dict[Workflow, AnalysisStarterScenario] = {
        Workflow.NALLO: AnalysisStarterScenario(
            nextflow_config=NalloConfig,
            params_file_creator=NalloParamsFileCreator,
            pipeline_extension=PipelineExtension,
            sample_sheet_creator=NalloSampleSheetCreator,
            store="mock_store_for_nallo_file_creators",
        ),
        Workflow.RAREDISEASE: AnalysisStarterScenario(
            nextflow_config=RarediseaseConfig,
            params_file_creator=RarediseaseParamsFileCreator,
            pipeline_extension=PipelineExtension,
            sample_sheet_creator=RarediseaseSampleSheetCreator,
            store="mock_store_for_raredisease_file_creators",
        ),
        Workflow.RNAFUSION: AnalysisStarterScenario(
            nextflow_config=RnafusionConfig,
            params_file_creator=RNAFusionParamsFileCreator,
            pipeline_extension=PipelineExtension,
            sample_sheet_creator=RNAFusionSampleSheetCreator,
            store="mock_store_for_rnafusion_file_creators",
        ),
        Workflow.TAXPROFILER: AnalysisStarterScenario(
            nextflow_config=TaxprofilerConfig,
            params_file_creator=TaxprofilerParamsFileCreator,
            pipeline_extension=PipelineExtension,
            sample_sheet_creator=TaxprofilerSampleSheetCreator,
            store="mock_store_for_taxprofiler_file_creators",
        ),
        Workflow.TOMTE: AnalysisStarterScenario(
            nextflow_config=TomteConfig,
            params_file_creator=TomteParamsFileCreator,
            pipeline_extension=TomteExtension,
            sample_sheet_creator=TomteSampleSheetCreator,
            store="mock_store_for_tomte_file_creators",
        ),
    }

    def configurator_and_expected_case_config(
        workflow: Workflow,
    ) -> tuple[NextflowConfigurator, NextflowCaseConfig]:
        scenario: AnalysisStarterScenario = scenarios[workflow]
        nextflow_config_dict: dict = get_nextflow_config_dict(workflow)

        configurator = NextflowConfigurator(
            config_file_creator=create_autospec(NextflowConfigFileCreator),
            params_file_creator=create_autospec(scenario.params_file_creator),
            pipeline_extension=create_autospec(scenario.pipeline_extension),
            pipeline_config=scenario.nextflow_config(**nextflow_config_dict),
            sample_sheet_creator=create_autospec(scenario.sample_sheet_creator),
            store=request.getfixturevalue(scenario.store),
        )

        expected_case_config = NextflowCaseConfig(**get_nextflow_case_config_dict(workflow))

        return configurator, expected_case_config

    return configurator_and_expected_case_config
