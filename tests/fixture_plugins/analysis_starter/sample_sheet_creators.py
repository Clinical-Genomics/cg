from unittest.mock import create_autospec

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.raredisease import (
    RarediseaseSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion import (
    RNAFusionSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.taxprofiler import (
    TaxprofilerSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.tomte_sample_sheet_creator import (
    TomteSampleSheetCreator,
)
from cg.store.store import Store


@pytest.fixture
def raredisease_sample_sheet_creator(
    mock_store_for_raredisease_file_creators: Store,
    mock_housekeeper_for_nf_sample_sheet: HousekeeperAPI,
) -> RarediseaseSampleSheetCreator:
    return RarediseaseSampleSheetCreator(
        store=mock_store_for_raredisease_file_creators,
        housekeeper_api=mock_housekeeper_for_nf_sample_sheet,
    )


@pytest.fixture
def rnafusion_sample_sheet_creator(
    mock_store_for_rnafusion_file_creators: Store,
    mock_housekeeper_for_nf_sample_sheet: HousekeeperAPI,
) -> RNAFusionSampleSheetCreator:
    return RNAFusionSampleSheetCreator(
        store=mock_store_for_rnafusion_file_creators,
        housekeeper_api=mock_housekeeper_for_nf_sample_sheet,
    )


@pytest.fixture
def taxprofiler_sample_sheet_creator(
    mock_store_for_taxprofiler_file_creators: Store,
    mock_housekeeper_for_nf_sample_sheet: HousekeeperAPI,
) -> TaxprofilerSampleSheetCreator:
    return TaxprofilerSampleSheetCreator(
        store=mock_store_for_taxprofiler_file_creators,
        housekeeper_api=mock_housekeeper_for_nf_sample_sheet,
    )


@pytest.fixture
def tomte_sample_sheet_creator(
    mock_housekeeper_for_nf_sample_sheet: HousekeeperAPI,
) -> TomteSampleSheetCreator:
    return TomteSampleSheetCreator(
        store=create_autospec(Store),
        housekeeper_api=mock_housekeeper_for_nf_sample_sheet,
    )
