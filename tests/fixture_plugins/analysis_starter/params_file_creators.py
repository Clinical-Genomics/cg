from unittest.mock import create_autospec

import pytest

from cg.apps.lims import LimsAPI
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.rnafusion import (
    RNAFusionParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.taxprofiler import (
    TaxprofilerParamsFileCreator,
)
from cg.store.store import Store


@pytest.fixture
def nextflow_params_file_path() -> str:
    """Path to Nextflow params file."""
    return "params/nextflow_params.yaml"


@pytest.fixture
def raredisease_params_file_creator(
    mock_store_for_raredisease_file_creators: Store,
    nextflow_params_file_path: str,
) -> RarediseaseParamsFileCreator:
    """Fixture to provide a RarediseaseParamsFileCreator with a mock store."""
    lims: LimsAPI = create_autospec(LimsAPI)
    lims.capture_kit.return_value = "capture_kit"
    return RarediseaseParamsFileCreator(
        store=mock_store_for_raredisease_file_creators,
        lims=lims,
        params=nextflow_params_file_path,
    )


@pytest.fixture
def rnafusion_params_file_creator(
    nextflow_params_file_path: str,
) -> RNAFusionParamsFileCreator:
    return RNAFusionParamsFileCreator(nextflow_params_file_path)


@pytest.fixture
def taxprofiler_params_file_creator(
    nextflow_params_file_path: str,
) -> TaxprofilerParamsFileCreator:
    return TaxprofilerParamsFileCreator(nextflow_params_file_path)
