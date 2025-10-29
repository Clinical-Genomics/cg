from pathlib import Path
from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from cg.services.analysis_starter.configurator.file_creators.nextflow import config_file
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
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
