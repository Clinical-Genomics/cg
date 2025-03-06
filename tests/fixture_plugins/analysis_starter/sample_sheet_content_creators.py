import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.sample_sheet.raredisease import (
    RarediseaseSampleSheetContentCreator,
)


@pytest.fixture
def raredisease_sample_sheet_content_creator(
    raredisease_context: CGConfig,
) -> RarediseaseSampleSheetContentCreator:
    return RarediseaseSampleSheetContentCreator(
        store=raredisease_context.status_db,
        housekeeper_api=raredisease_context.housekeeper_api,
        lims=raredisease_context.lims_api,
    )
