from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.file_creators.nextflow import config_file
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.store.store import Store


@pytest.fixture
def nextflow_cluster_options() -> str:
    return f'process.clusterOptions = "-A development --qos={SlurmQos.NORMAL}"\n'


@pytest.fixture
def nextflow_config_base_content(
    nf_analysis_pipeline_config_path: Path,
    nf_analysis_platform_config_path: Path,
    nf_analysis_pipeline_resource_optimisation_path: Path,
) -> str:
    content: str = (
        "\n"
        + nf_analysis_platform_config_path.read_text()
        + "\n"
        + nf_analysis_pipeline_config_path.read_text()
        + "\n"
        + nf_analysis_pipeline_resource_optimisation_path.read_text()
    )
    return content


@pytest.fixture
def expected_nextflow_config_content(
    nextflow_cluster_options: str,
    nextflow_config_base_content: str,
) -> str:
    return nextflow_cluster_options + nextflow_config_base_content + "\n"


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


def test_nextflow_config_file_content(
    nextflow_config_file_creator: NextflowConfigFileCreator,
    nextflow_case_id: str,
    nextflow_case_path: Path,
    expected_nextflow_config_content: str,
    mocker: MockerFixture,
):
    """Test that a Nextflow config file content is created correctly for all pipelines."""
    # GIVEN a Nextflow config content creator and a case id

    # GIVEN a writer mock
    write_mock: MagicMock = mocker.patch.object(config_file, "write_txt", return_value=None)

    # WHEN creating a Nextflow config file
    file_path = Path(nextflow_case_path, f"{nextflow_case_id}_nextflow_config.json")
    nextflow_config_file_creator.create(case_id=nextflow_case_id, file_path=file_path)

    # THEN the content of the file is the expected
    write_mock.assert_called_once_with(
        file_path=file_path, content=expected_nextflow_config_content
    )
