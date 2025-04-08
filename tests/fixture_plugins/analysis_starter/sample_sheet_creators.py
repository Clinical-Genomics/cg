import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.raredisease import (
    RarediseaseSampleSheetCreator,
)


@pytest.fixture
def raredisease_sample_sheet_creator(
    raredisease_context: CGConfig,
) -> RarediseaseSampleSheetCreator:
    return RarediseaseSampleSheetCreator(
        store=raredisease_context.status_db,
        housekeeper_api=raredisease_context.housekeeper_api,
        lims=raredisease_context.lims_api,
    )
