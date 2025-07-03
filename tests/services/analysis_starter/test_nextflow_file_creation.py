from pathlib import Path
from unittest import mock

import pytest
from pytest_mock import MockerFixture

from cg.apps.scout.scoutapi import ScoutAPI
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.gene_panel import (
    GenePanelFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet import (
    abstract,
    rnafusion,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.abstract import (
    NextflowSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion import (
    RNAFusionSampleSheetCreator,
)


@pytest.mark.parametrize(
    "file_creator_fixture, expected_content_fixture, mock_writer",
    [
        (
            "raredisease_params_file_creator2",
            "expected_raredisease_params_file_content",
            "write_raredisease_mock",
        ),
        (
            "rnafusion_params_file_creator",
            "expected_rnafusion_params_file_content",
            "write_rnafusion_mock",
        ),
    ],
    ids=["raredisease", "rnafusion"],
)
def test_nextflow_params_file_creator(
    file_creator_fixture: str,
    expected_content_fixture: str,
    mock_writer: str,
    nextflow_case_path: Path,
    nextflow_sample_sheet_path: Path,
    nextflow_case_id: str,
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
):
    """Test that the Raredisease params file creator is initialized correctly."""
    # GIVEN a case id, case path and sample sheet path

    # GIVEN a ParamsFileCreator
    params_file_creator: ParamsFileCreator = request.getfixturevalue(file_creator_fixture)

    # WHEN creating the params file
    write_mock: mocker.MagicMock = request.getfixturevalue(mock_writer)
    params_file_creator.create(
        case_id=nextflow_case_id,
        case_path=nextflow_case_path,
        sample_sheet_path=nextflow_sample_sheet_path,
    )

    # THEN the file should have been written with the expected content
    file_path: Path = params_file_creator.get_file_path(
        case_id=nextflow_case_id, case_path=nextflow_case_path
    )
    expected_params_file_content: dict = request.getfixturevalue(expected_content_fixture)
    write_mock.assert_called_once_with(file_path=file_path, content=expected_params_file_content)


@pytest.mark.parametrize(
    "file_creator_fixture, case_id_fixture, expected_content_fixture",
    [
        (
            "raredisease_config_file_creator",
            "raredisease_case_id",
            "expected_raredisease_config_content",
        )
    ],
    ids=["raredisease"],
)
def test_nextflow_config_file_content(
    file_creator_fixture: str,
    case_id_fixture: str,
    expected_content_fixture: str,
    request: pytest.FixtureRequest,
):
    """Test that a Nextflow config file content is created correctly for all pipelines."""
    # GIVEN a Nextflow config content creator and a case id
    file_creator: NextflowConfigFileCreator = request.getfixturevalue(file_creator_fixture)
    case_id: str = request.getfixturevalue(case_id_fixture)

    # WHEN creating a Nextflow config file
    content: str = file_creator._get_content(case_id)

    # THEN the content of the file is the expected
    expected_content: str = request.getfixturevalue(expected_content_fixture)
    assert content.rstrip() == expected_content.rstrip()


@pytest.mark.parametrize(
    "file_creator_fixture, case_id_fixture, expected_content_fixture",
    [
        (
            "raredisease_sample_sheet_creator",
            "raredisease_case_id",
            "raredisease_sample_sheet_expected_content",
        )
    ],
    ids=["raredisease"],
)
def test_nextflow_sample_sheet_content(
    file_creator_fixture: str,
    case_id_fixture: str,
    expected_content_fixture: str,
    request: pytest.FixtureRequest,
):
    """Test that the sample sheet content is created correctly."""
    # GIVEN a sample sheet content creator, a case id and a case path
    file_creator: NextflowSampleSheetCreator = request.getfixturevalue(file_creator_fixture)
    case_id: str = request.getfixturevalue(case_id_fixture)

    # WHEN creating a sample sheet
    content: list[list[str]] = file_creator._get_content(case_id=case_id)

    # THEN the content of the file is the expected
    expected_content: str = request.getfixturevalue(expected_content_fixture)
    assert content == expected_content


def test_rnafusion_sample_sheet_creator(
    nextflow_case_id: str,
    nextflow_case_path: Path,
    rnafusion_sample_sheet_content_list: list[list[str]],
    rnafusion_sample_sheet_creator: RNAFusionSampleSheetCreator,
    mocker: MockerFixture,
):

    write_mock = mocker.patch.object(rnafusion, "write_csv")
    mocker.patch.object(
        abstract,
        "read_gzip_first_line",
        side_effect=[
            "@ST-E00201:173:HCXXXXX:1:2106:22516:34834/1",
            "@ST-E00201:173:HCXXXXX:1:2106:22516:34834/2",
        ],
    )
    mocker.patch.object(Path, "is_file", return_value=True)
    rnafusion_sample_sheet_creator.create(case_id=nextflow_case_id, case_path=nextflow_case_path)
    write_mock.assert_called_with(
        content=rnafusion_sample_sheet_content_list,
        file_path=rnafusion_sample_sheet_creator.get_file_path(
            case_path=nextflow_case_path, case_id=nextflow_case_id
        ),
    )


@pytest.mark.parametrize(
    "file_creator_fixture, case_id_fixture, expected_content_fixture",
    [
        (
            "raredisease_gene_panel_creator",
            "raredisease_case_id",
            "raredisease_gene_panel_file_content",
        )
    ],
    ids=["raredisease"],
)
def test_gene_panel_file_content(
    file_creator_fixture: str,
    case_id_fixture: str,
    expected_content_fixture: str,
    request: pytest.FixtureRequest,
):
    """Test that the gene panel file content is created correctly."""
    # GIVEN a gene panel file content creator and a case path
    file_creator: GenePanelFileCreator = request.getfixturevalue(file_creator_fixture)
    case_id: str = request.getfixturevalue(case_id_fixture)

    # GIVEN a mock of Scout gene panels
    expected_content: list[str] = request.getfixturevalue(expected_content_fixture)

    # WHEN creating a gene panel file
    with mock.patch.object(ScoutAPI, "export_panels", return_value=expected_content):
        content: list[str] = file_creator._get_content(case_id)

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
