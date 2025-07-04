from pathlib import Path
from unittest.mock import create_autospec

import pytest
from pytest_mock import MockFixture

from cg.apps.lims import LimsAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file import raredisease
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease import (
    RarediseaseParamsFileCreator,
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
def raredisease_params_file_creator2(
    mock_store_for_raredisease_params_file_creator: Store,
    nf_analysis_pipeline_params_path: Path,
    mocker: MockFixture,
) -> RarediseaseParamsFileCreator:
    """Fixture to provide a RarediseaseParamsFileCreator with a mock store."""
    lims = create_autospec(LimsAPI)
    lims.capture_kit.return_value = "capture_kit"
    mocker.patch.object(raredisease, "read_yaml", return_value={"someparam": "something"})
    mocker.patch.object(raredisease, "write_csv", return_value=None)
    return RarediseaseParamsFileCreator(
        store=mock_store_for_raredisease_params_file_creator,
        lims=lims,
        params=nf_analysis_pipeline_params_path.as_posix(),
    )
