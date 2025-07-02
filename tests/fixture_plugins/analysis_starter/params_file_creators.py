from pathlib import Path
from unittest.mock import create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.lims import LimsAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file import (
    raredisease,
    rnafusion,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.rnafusion import (
    RNAFusionParamsFileCreator,
)
from cg.store.store import Store


@pytest.fixture
def raredisease_params_file_creator(
    raredisease_context: CGConfig,
) -> RarediseaseParamsFileCreator:
    return RarediseaseParamsFileCreator(
        store=raredisease_context.status_db,
        lims=raredisease_context.lims_api,
        params=raredisease_context.raredisease.params,
    )


@pytest.fixture
def rnafusion_params_file_creator(
    nf_analysis_pipeline_params_path: Path,
    nextflow_params_file_content: dict,
    mocker: MockerFixture,
) -> RNAFusionParamsFileCreator:
    mocker.patch.object(rnafusion, "read_yaml", return_value=nextflow_params_file_content)
    return RNAFusionParamsFileCreator(nf_analysis_pipeline_params_path.as_posix())


@pytest.fixture
def raredisease_params_file_creator2(
    mock_store_for_raredisease_params_file_creator: Store,
    nextflow_params_file_content: dict,
    nf_analysis_pipeline_params_path: Path,
    mocker: MockerFixture,
) -> RarediseaseParamsFileCreator:
    """Fixture to provide a RarediseaseParamsFileCreator with a mock store."""
    lims = create_autospec(LimsAPI)
    lims.capture_kit.return_value = "capture_kit"
    mocker.patch.object(raredisease, "read_yaml", return_value=nextflow_params_file_content)
    mocker.patch.object(raredisease, "write_csv", return_value=None)
    return RarediseaseParamsFileCreator(
        store=mock_store_for_raredisease_params_file_creator,
        lims=lims,
        params=nf_analysis_pipeline_params_path.as_posix(),
    )
