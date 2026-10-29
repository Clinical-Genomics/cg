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
    - file_type: non-mandatory-sample-type
      id: SAMPLEID
      mandatory: false
      paths:
        - PATHTOCASE/outputs/SAMPLENAME_sorted_md.cram
    - file_type: mandatory-case-multipath-type
      id: CASEID
      mandatory: true
      paths:
        - PATHTOCASE/output1/CASEID.json
        - PATHTOCASE/output2/CASEID.json
    """)


@pytest.fixture
def expected_case_deliverables_content() -> str:
    return dedent("""    ---
    - file_type: non-mandatory-sample-type
      id: sample_id_1
      mandatory: false
      paths:
      - path/to/case/outputs/sample-name-1_sorted_md.cram
    - file_type: non-mandatory-sample-type
      id: sample_id_2
      mandatory: false
      paths:
      - path/to/case/outputs/sample-name-2_sorted_md.cram
    - file_type: mandatory-case-multipath-type
      id: case_id
      mandatory: true
      paths:
      - path/to/case/output1/case_id.json
      - path/to/case/output2/case_id.json
    """)


def test_create(
    expected_case_deliverables_content: str, pipeline_deliverables_content: str, fs: FakeFilesystem
):
    # GIVEN a pipeline deliverables file
    fs.create_file(
        file_path=Path("trana_deliverables.yaml"), contents=pipeline_deliverables_content
    )

    # GIVEN a case with samples in StatusDB
    sample_1 = create_autospec(Sample, internal_id="sample_id_1")
    sample_1.name = "sample-name-1"
    sample_2 = create_autospec(Sample, internal_id="sample_id_2")
    sample_2.name = "sample-name-2"
    case = create_autospec(Case, internal_id="case_id", samples=[sample_1, sample_2])
    status_db = create_autospec(Store)
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a CaseDeliverablesFileCreator
    file_creator = CaseDeliverablesFileCreator(status_db)

    # WHEN creating the case_deliverables file
    file_creator.create(
        case_id="case_id",
        file_path=Path("case_id_deliverables.yaml"),
        pipeline_deliverables=Path("trana_deliverables.yaml"),
    )

    # THEN a file will be written with the correct content
    assert Path("case_id_deliverables.yaml").read_text() == expected_case_deliverables_content
