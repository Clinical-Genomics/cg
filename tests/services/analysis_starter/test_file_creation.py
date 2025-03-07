from pathlib import Path

import pytest

from cg.services.analysis_starter.configurator.file_creators.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)


@pytest.mark.parametrize(
    "file_creator_fixture, case_path_fixture, expected_content_fixture",
    [
        (
            "raredisease_config_file_creator",
            "raredisease_case_path",
            "expected_raredisease_config_content",
        )
    ],
    ids=["raredisease"],
)
def test_create_nextflow_config_file_content(
    file_creator_fixture: str,
    case_path_fixture: str,
    expected_content_fixture: str,
    request: pytest.FixtureRequest,
):
    """Test that a Nextflow config file content is created correctly for all pipelines."""
    # GIVEN a Nextflow config content creator and a case id
    file_creator: NextflowConfigFileCreator = request.getfixturevalue(file_creator_fixture)
    case_path: Path = request.getfixturevalue(case_path_fixture)

    # WHEN creating a Nextflow config file
    content: str = file_creator._get_content(case_path)

    # THEN the content of the file is the expected
    expected_content: str = request.getfixturevalue(expected_content_fixture)
    assert content.rstrip() == expected_content.rstrip()


@pytest.mark.parametrize(
    "content_creator_fixture, case_id_fixture, case_path_fixture, expected_content_fixture",
    [
        (
            "raredisease_params_file_creator",
            "raredisease_case_id",
            "raredisease_case_path",
            "expected_raredisease_params_file_content",
        )
    ],
    ids=["raredisease"],
)
def test_create_params_file_content(
    content_creator_fixture: str,
    case_id_fixture: str,
    case_path_fixture: str,
    expected_content_fixture: str,
    raredisease_sample_sheet_path: Path,
    request: pytest.FixtureRequest,
):
    """Test that the params file content is created correctly for all pipelines."""
    # GIVEN a params file content creator and a case id
    content_creator: RarediseaseParamsFileCreator = request.getfixturevalue(content_creator_fixture)
    case_id: str = request.getfixturevalue(case_id_fixture)
    case_path: Path = request.getfixturevalue(case_path_fixture)

    # WHEN creating a params file
    content: dict = content_creator._get_content(
        case_id=case_id, case_path=case_path, sample_sheet_path=raredisease_sample_sheet_path
    )

    # THEN the content of the file is the expected
    expected_content: str = request.getfixturevalue(expected_content_fixture)
    assert content == expected_content
