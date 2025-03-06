import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.extensions.raredisease import RarediseaseExtension
from cg.services.analysis_starter.configurator.file_creators.config_file import (
    NextflowConfigFileContentCreator,
)
from cg.services.analysis_starter.configurator.file_creators.params_file.raredisease import (
    RarediseaseParamsFileContentCreator,
)
from cg.services.analysis_starter.configurator.file_creators.sample_sheet.raredisease import (
    RarediseaseSampleSheetContentCreator,
)


@pytest.fixture
def raredisease_configurator(
    raredisease_context: CGConfig,
    raredisease_config_file_content_creator: NextflowConfigFileContentCreator,
    raredisease_sample_sheet_content_creator: RarediseaseSampleSheetContentCreator,
    raredisease_params_content_creator: RarediseaseParamsFileContentCreator,
) -> RarediseaseExtension:
    return RarediseaseExtension(
        store=raredisease_context.status_db,
        config=raredisease_context.raredisease,
        housekeeper_api=raredisease_context.housekeeper_api,
        lims=raredisease_context.lims_api,
        config_content_creator=raredisease_config_file_content_creator,
        sample_sheet_content_creator=raredisease_sample_sheet_content_creator,
        params_content_creator=raredisease_params_content_creator,
    )
