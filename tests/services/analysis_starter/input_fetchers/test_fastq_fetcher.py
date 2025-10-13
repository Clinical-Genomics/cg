from unittest.mock import Mock, create_autospec

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.analysis_starter.input_fetcher.implementations.fastq_fetcher import FastqFetcher
from cg.store.models import Case, Sample
from cg.store.store import Store


def test_ensure_files_are_ready():
    sample: Sample = create_autospec(Sample)
    case: Case = create_autospec(Case, samples=[sample])
    status_db: Store = create_autospec(Store)
    status_db.get_case_by_internal_id = Mock(return_value=case)

    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    housekeeper_api.get_archived_files_for_bundle = Mock(return_value=[])

    fastq_fetcher = FastqFetcher(
        compress_api=Mock(),
        housekeeper_api=housekeeper_api,
        spring_archive_api=Mock(),
        status_db=status_db,
    )

    fastq_fetcher.ensure_files_are_ready("case_id")
