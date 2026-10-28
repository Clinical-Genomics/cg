from pathlib import Path

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
    return """- id: SAMPLEID
  path: PATHTOCASE/alignment/SAMPLEID_sorted_md.cram
  file_type: cram-picard-duplicates
  mandatory: false
- id: SAMPLEID
  paths: 
  - PATHTOCASE/alignment/SAMPLEID_sorted_md.cram.crai
  file_type: cram-index-picard-duplicates
  mandatory: false
- id: SAMPLEID
  path: PATHTOCASE/alignment/SAMPLEID_mt_subsample.bam
  file_type: bam-mt
  mandatory: false
    """

def test_create(fs: FakeFilesystem):
    # GIVEN a pipeline deliverables file
    fs.create_file(file_path=Path("trana_deliverables.yaml"), contents=)

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
        file_path=Path("case_id_deliverables.yaml"),
        pipeline_deliverables=Path("trana_deliverables.yaml"),
    )

    # THEN a file will be written with the correct content