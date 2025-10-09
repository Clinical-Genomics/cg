from pathlib import Path

import pytest

from cg.apps.lims import LimsAPI
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.store.store import Store


@pytest.fixture
def microsalt_config_file_creator(
    microsalt_store: Store, lims_api: LimsAPI
) -> MicrosaltConfigFileCreator:
    return MicrosaltConfigFileCreator(
        lims_api=lims_api, queries_path="/dev/null", store=microsalt_store
    )


@pytest.fixture
def nextflow_config_file_creator(
    mock_store_for_nextflow_config_file_creation: Store,
    nf_analysis_platform_config_path: Path,
    nf_analysis_pipeline_config_path: Path,
    nf_analysis_pipeline_resource_optimisation_path: Path,
) -> NextflowConfigFileCreator:
    return NextflowConfigFileCreator(
        store=mock_store_for_nextflow_config_file_creation,
        platform=nf_analysis_platform_config_path.as_posix(),
        workflow_config_path=nf_analysis_pipeline_config_path.as_posix(),
        resources=nf_analysis_pipeline_resource_optimisation_path.as_posix(),
        account="development",
    )
