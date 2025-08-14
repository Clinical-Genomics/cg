from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.services.analysis_starter.configurator.file_creators.nextflow import config_file
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet import (
    creator as samplesheet_creator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowSampleSheetCreator,
)


@pytest.mark.parametrize(
    "workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER]
)
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


def test_get_samplesheet_path(
    rnafusion_sample_sheet_creator: NextflowSampleSheetCreator,
    nextflow_case_id: str,
    nextflow_case_path: Path,
):
    """Test that the sample sheet path is constructed correctly."""
    # GIVEN a Nextflow sample sheet creator and a case id

    # WHEN getting the sample sheet path
    sample_sheet_path: Path = rnafusion_sample_sheet_creator.get_file_path(
        case_id=nextflow_case_id, case_path=nextflow_case_path
    )

    # THEN the path should end with 'samplesheet.csv'
    expected_path = Path(nextflow_case_path, f"{nextflow_case_id}_samplesheet.csv")
    assert sample_sheet_path == expected_path


@pytest.mark.parametrize(
    "workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER]
)
def test_nextflow_sample_sheet_creators(
    workflow: Workflow,
    sample_sheet_scenario: dict,
    nextflow_case_id: str,
    nextflow_case_path: Path,
    mocker: MockerFixture,
):
    # GIVEN a sample sheet creator, an expected output and a mocked file writer
    sample_sheet_creator, expected_content = sample_sheet_scenario[workflow]
    write_mock: mocker.MagicMock = mocker.patch.object(samplesheet_creator, "write_csv")

    # GIVEN a pair of Fastq files that have a header
    mocker.patch.object(
        samplesheet_creator,
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


def test_parse_fastq_header_raises_error():
    # GIVEN a faulty FASTQ Header

    with pytest.raises(TypeError):
        # WHEN parsing the header
        # THEN the correct error is raised
        NextflowSampleSheetCreator._parse_fastq_header(line="Not a Fastq header")
