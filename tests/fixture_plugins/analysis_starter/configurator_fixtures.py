import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.file_creators.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.sample_sheet.raredisease import (
    RarediseaseSampleSheetContentCreator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator


@pytest.fixture
def raredisease_configurator(
    raredisease_context: CGConfig,
    raredisease_config_file_content_creator: NextflowConfigFileCreator,
    raredisease_sample_sheet_content_creator: RarediseaseSampleSheetContentCreator,
    raredisease_params_content_creator: RarediseaseParamsFileCreator,
    raredisease_extension: PipelineExtension,
) -> NextflowConfigurator:
    return NextflowConfigurator(
        store=raredisease_context.status_db,
        config=raredisease_context.raredisease,
        housekeeper_api=raredisease_context.housekeeper_api,
        lims=raredisease_context.lims_api,
        config_file_creator=raredisease_config_file_content_creator,
        sample_sheet_creator=raredisease_sample_sheet_content_creator,
        params_file_creator=raredisease_params_content_creator,
        pipeline_extension=raredisease_extension,
    )
