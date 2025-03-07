from pathlib import Path
from unittest import mock

import pytest

from cg.apps.scout.scoutapi import ScoutAPI
from cg.services.analysis_starter.configurator.file_creators.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.sample_sheet.abstract import (
    NextflowSampleSheetCreator,
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
def test_nextflow_config_file_content(
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
    "file_creator_fixture, case_id_fixture, case_path_fixture, expected_content_fixture",
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
def test_params_file_content(
    file_creator_fixture: str,
    case_id_fixture: str,
    case_path_fixture: str,
    expected_content_fixture: str,
    raredisease_sample_sheet_path: Path,
    request: pytest.FixtureRequest,
):
    """Test that the params file content is created correctly for all pipelines."""
    # GIVEN a params file content creator and a case id
    content_creator: RarediseaseParamsFileCreator = request.getfixturevalue(file_creator_fixture)
    case_id: str = request.getfixturevalue(case_id_fixture)
    case_path: Path = request.getfixturevalue(case_path_fixture)

    # WHEN creating a params file
    content: dict = content_creator._get_content(
        case_id=case_id, case_path=case_path, sample_sheet_path=raredisease_sample_sheet_path
    )

    # THEN the content of the file is the expected
    expected_content: str = request.getfixturevalue(expected_content_fixture)
    assert content == expected_content


@pytest.mark.parametrize(
    "file_creator_fixture, case_id_fixture, case_path_fixture, expected_content_fixture",
    [
        (
            "raredisease_sample_sheet_creator",
            "raredisease_case_id",
            "raredisease_case_path",
            "raredisease_sample_sheet_content",
        )
    ],
    ids=["raredisease"],
)
def test_nextflow_sample_sheet_content(
    file_creator_fixture: str,
    case_id_fixture: str,
    case_path_fixture: str,
    expected_content_fixture: str,
    request: pytest.FixtureRequest,
):
    """Test that the sample sheet content is created correctly."""
    # GIVEN a sample sheet content creator, a case id and a case path
    file_creator: NextflowSampleSheetCreator = request.getfixturevalue(file_creator_fixture)
    case_id: str = request.getfixturevalue(case_id_fixture)
    case_path: Path = request.getfixturevalue(case_path_fixture)

    # WHEN creating a sample sheet
    content: list[list[str]] = file_creator._get_content(case_id=case_id, case_path=case_path)

    # THEN the content of the file is the expected
    expected_content: str = request.getfixturevalue(expected_content_fixture)
    assert content == expected_content


@pytest.mark.parametrize(
    "file_creator_fixture, case_path_fixture, expected_content_fixture",
    [
        (
            "raredisease_gene_panel_creator",
            "raredisease_case_path",
            "raredisease_gene_panel_file_content",
        )
    ],
    ids=["raredisease"],
)
def test_gene_panel_file_content(
    file_creator_fixture: str,
    case_path_fixture: str,
    expected_content_fixture: str,
    request: pytest.FixtureRequest,
):
    """Test that the gene panel file content is created correctly."""
    # GIVEN a gene panel file content creator and a case path
    file_creator: GenePanelFileCreator = request.getfixturevalue(file_creator_fixture)
    case_path: Path = request.getfixturevalue(case_path_fixture)

    # GIVEN a mock of Scout gene panels
    expected_content: list[str] = request.getfixturevalue(expected_content_fixture)

    # WHEN creating a gene panel file
    with mock.patch.object(ScoutAPI, "export_panels", return_value=expected_content):
        content: list[str] = file_creator._get_content(case_path)

    # THEN the content of the file is the expected

    assert content == expected_content


def test_managed_variants_content(
    raredisease_managed_variants_creator: ManagedVariantsFileCreator,
    raredisease_case_id: str,
    raredisease_managed_variants_file_content: list[str],
):
    """Test that the managed variants file content is created correctly."""
    # GIVEN a Raredisease managed variants file content creator and a case path

    # GIVEN a mock of Scout variants

    # WHEN creating a managed variants file
    expected_content_fixture: list[str] = raredisease_managed_variants_file_content
    with mock.patch.object(
        ScoutAPI, "export_managed_variants", return_value=expected_content_fixture
    ):
        content: list[str] = raredisease_managed_variants_creator._get_content(raredisease_case_id)

    # THEN the content of the file is the expected
    assert content == expected_content_fixture
