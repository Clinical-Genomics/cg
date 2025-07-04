from pathlib import Path
from unittest import mock

import pytest
from pytest_mock import MockerFixture

from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Workflow
from cg.services.analysis_starter.configurator.file_creators.nextflow import config_file
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.gene_panel import (
    GenePanelFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet import creator
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowSampleSheetCreator,
)


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_nextflow_params_file_creator(
    workflow: Workflow,
    params_file_scenario: dict,
    nextflow_case_path: Path,
    nextflow_sample_sheet_path: Path,
    nextflow_case_id: str,
):
    """Test that the Raredisease params file creator is initialized correctly."""
    # GIVEN a params file creator, an expected output and a mocked file writer
    file_creator, expected_content, write_yaml_mock = params_file_scenario[workflow]

    # WHEN creating the params file
    file_creator.create(
        case_id=nextflow_case_id,
        case_path=nextflow_case_path,
        sample_sheet_path=nextflow_sample_sheet_path,
    )

    # THEN the file should have been written with the expected content
    file_path: Path = file_creator.get_file_path(
        case_id=nextflow_case_id, case_path=nextflow_case_path
    )
    write_yaml_mock.assert_called_once_with(file_path=file_path, content=expected_content)


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
    write_mock: mocker.MagicMock = mocker.patch.object(config_file, "write_txt", return_value=None)

    # WHEN creating a Nextflow config file
    nextflow_config_file_creator.create(case_id=nextflow_case_id, case_path=nextflow_case_path)

    # THEN the content of the file is the expected
    file_path = Path(nextflow_case_path, f"{nextflow_case_id}_nextflow_config.json")
    write_mock.assert_called_once_with(
        file_path=file_path, content=expected_nextflow_config_content
    )


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_nextflow_sample_sheet_creators(
    workflow: Workflow,
    sample_sheet_scenario: dict,
    nextflow_case_id: str,
    nextflow_case_path: Path,
    mocker: MockerFixture,
):
    # GIVEN a sample sheet creator, an expected output and a mocked file writer
    sample_sheet_creator, expected_content = sample_sheet_scenario[workflow]
    write_mock: mocker.MagicMock = mocker.patch.object(creator, "write_csv")

    # GIVEN a pair of Fastq files that have a header
    mocker.patch.object(
        creator,
        "read_gzip_first_line",
        side_effect=[
            "@ST-E00201:173:HCXXXXX:1:2106:22516:34834/1",
            "@ST-E00201:173:HCXXXXX:1:2106:22516:34834/2",
        ],
    )
    # GIVEN that the files exist
    mocker.patch.object(Path, "is_file", return_value=True)

    # WHEN creating the sample sheet
    sample_sheet_creator.create(case_id=nextflow_case_id, case_path=nextflow_case_path)

    # THEN the sample sheet should have been written to the correct path with the correct content
    write_mock.assert_called_with(
        content=expected_content,
        file_path=sample_sheet_creator.get_file_path(
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


def test_parse_fastq_header_raises_error():
    # GIVEN a faulty FASTQ Header

    with pytest.raises(TypeError):
        # WHEN parsing the header
        # THEN the correct error is raised
        NextflowSampleSheetCreator._parse_fastq_header(line="Not a Fastq header")
