import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.params_file.raredisease import (
    RarediseaseParamsFileContentCreator,
)
from cg.services.analysis_starter.configurator.file_creators.sample_sheet.raredisease import (
    RarediseaseSampleSheetContentCreator,
)
from cg.services.analysis_starter.configurator.implementations.raredisease import (
    RarediseaseConfigurator,
)


@pytest.fixture
def raredisease_configurator(
    raredisease_context: CGConfig,
    raredisease_sample_sheet_content_creator: RarediseaseSampleSheetContentCreator,
    raredisease_params_content_creator: RarediseaseParamsFileContentCreator,
) -> RarediseaseConfigurator:
    return RarediseaseConfigurator(
        store=raredisease_context.status_db,
        config=raredisease_context.raredisease,
        housekeeper_api=raredisease_context.housekeeper_api,
        lims=raredisease_context.lims_api,
        sample_sheet_content_creator=raredisease_sample_sheet_content_creator,
        params_content_creator=raredisease_params_content_creator,
    )
