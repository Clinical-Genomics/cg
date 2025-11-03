from unittest.mock import Mock, create_autospec

import pytest
from housekeeper.store.models import File
from sqlalchemy.orm import Query

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import AnalysisNotReadyError
from cg.services.analysis_starter.input_fetcher.implementations.bam_fetcher import BamFetcher
from cg.store.models import Case, Sample
from cg.store.store import Store


def test_ensure_files_are_ready_success():
    # GIVEN a case with all BAM files on disk
    status_db: Store = create_autospec(Store)
    sample: Sample = create_autospec(Sample)
    case: Case = create_autospec(Case, samples=[sample])
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a BamFetcher
    bam_fetcher = BamFetcher(status_db=status_db, housekeeper_api=Mock())

    # WHEN ensuring that all files are ready
    bam_fetcher.ensure_files_are_ready("case_id")

    # THEN no error is raised


def test_ensure_files_are_ready_failure():
    # GIVEN a case with all BAM files on disk
    status_db: Store = create_autospec(Store)
    sample: Sample = create_autospec(Sample)
    case: Case = create_autospec(Case, samples=[sample])
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    housekeeper_api.files = Mock(
        return_value=create_autospec(
            Query, all=Mock(return_value=[create_autospec(File, full_path="non/existing/file")])
        )
    )

    # GIVEN a BamFetcher
    bam_fetcher = BamFetcher(status_db=status_db, housekeeper_api=Mock())

    # WHEN ensuring that all files are ready
    # THEN an error is raised
    with pytest.raises(AnalysisNotReadyError):
        bam_fetcher.ensure_files_are_ready("case_id")
