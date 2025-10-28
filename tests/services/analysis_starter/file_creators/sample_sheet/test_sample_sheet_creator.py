from pathlib import Path
from unittest.mock import MagicMock, Mock, create_autospec

import pytest
from housekeeper.store.models import File
from pytest_mock import MockerFixture
from sqlalchemy import Case

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet import (
    creator as samplesheet_creator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet import nallo
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.nallo import (
    NalloSampleSheetCreator,
)
from cg.store.models import CaseSample, Sample
from cg.store.store import Store


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
    write_mock: MagicMock = mocker.patch.object(samplesheet_creator, "write_csv")

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
    file_path = Path(nextflow_case_path, f"{nextflow_case_id}_samplesheet.csv")
    sample_sheet_creator.create(case_id=nextflow_case_id, file_path=file_path)

    # THEN the sample sheet should have been written to the correct path with the correct content
    write_mock.assert_called_with(content=expected_content, file_path=file_path)


def test_create_nallo_sample_sheet(
    expected_nallo_sample_sheet_content: list[list[str]], mocker: MockerFixture
):

    # GIVEN a Nallo case in StatusDB
    case_id = "nallo_case"
    case_sample = create_autospec(
        CaseSample,
        get_maternal_sample_id="mother",
        get_paternal_sample_id="father",
        sample=create_autospec(Sample, internal_id="nallo_sample", sex="male"),
        status="affected",
    )
    case = create_autospec(Case, internal_id=case_id, links=[case_sample])
    case_sample.case = case

    status_db: Store = create_autospec(Store)
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN Housekeeper with two BAM files
    bam_file1: File = create_autospec(File, full_path="/a/path/to/file1.bam")
    bam_file2: File = create_autospec(File, full_path="/a/path/to/file2.bam")
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    housekeeper_api.files = Mock(return_value=[bam_file1, bam_file2])

    # GIVEN a sample sheet path
    sample_sheet_path = Path("sample", "sheet", "path.csv")

    # GIVEN a file writer
    write_mock: MagicMock = mocker.patch.object(nallo, "write_csv")

    # GIVEN a NalloSampleSheetCreator
    sample_sheet_creator = NalloSampleSheetCreator(
        housekeeper_api=housekeeper_api, status_db=status_db
    )

    # WHEN creating the sample sheet
    sample_sheet_creator.create(case_id=case_id, file_path=sample_sheet_path)

    # THEN the sample sheet should have been written to the correct path with the correct content
    write_mock.assert_called_once_with(
        file_path=sample_sheet_path, content=expected_nallo_sample_sheet_content
    )


def test_parse_fastq_header_raises_error():
    # GIVEN a faulty FASTQ Header

    with pytest.raises(TypeError):
        # WHEN parsing the header
        # THEN the correct error is raised
        NextflowSampleSheetCreator._parse_fastq_header(line="Not a Fastq header")
