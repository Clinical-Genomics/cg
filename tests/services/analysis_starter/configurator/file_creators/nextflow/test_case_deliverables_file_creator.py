from pathlib import Path
from textwrap import dedent

import pytest
from mock import Mock, create_autospec
from pyfakefs.fake_filesystem import FakeFilesystem

from cg.services.analysis_starter.configurator.file_creators.nextflow.case_deliverables_file_creator import (
    CaseDeliverablesFileCreator,
)
from cg.store.models import Case, Sample
from cg.store.store import Store


@pytest.fixture
def pipeline_deliverables_content() -> str:
    return dedent("""
    - file_type: cram-picard-duplicates
    id: SAMPLEID
    paths: 
      - PATHTOCASE/alignment/SAMPLEID_sorted_md.cram
    mandatory: false

    - file_type: copy-number-caller
    id: CASEID
    paths: 
      - PATHTOCASE/smncopynumbercaller/out/CASEID.json
    mandatory: true
    """)


@pytest.fixture
def expected_case_deliverables_content() -> str:
    return dedent("""
    - file_type: cram-picard-duplicates
    id: sample_1
    paths: 
      - path/to/case/alignment/sample_1_sorted_md.cram
    mandatory: false

    - file_type: cram-picard-duplicates
    id: sample_2
    paths: 
      - path/to/case/alignment/sample_2_sorted_md.cram
    mandatory: false

    - file_type: copy-number-caller
    id: case_id
    paths: 
      - path/to/case/smncopynumbercaller/out/case_id.json
    mandatory: true
    """)


def test_create(
    expected_case_deliverables_content: str, pipeline_deliverables_content: str, fs: FakeFilesystem
):
    # GIVEN a pipeline deliverables file
    fs.create_file(
        file_path=Path("trana_deliverables.yaml"), contents=pipeline_deliverables_content
    )

    # GIVEN a case with samples in StatusDB
    sample_1 = create_autospec(Sample, internal_id="sample_1")
    sample_2 = create_autospec(Sample, internal_id="sample_2")
    case = create_autospec(Case, internal_id="case_id", samples=[sample_1, sample_2])
    status_db = create_autospec(Store)
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a CaseDeliverablesFileCreator
    file_creator = CaseDeliverablesFileCreator(status_db)

    # WHEN creating the case_deliverables file
    file_creator.create(
        case_id="case_id",
        case_directory=Path("path/to/case"),
        file_path=Path("case_id_deliverables.yaml"),
        pipeline_deliverables=Path("trana_deliverables.yaml"),
    )

    # THEN a file will be written with the correct content
    assert Path("case_id_deliverables.yaml").read_text() == expected_case_deliverables_content
