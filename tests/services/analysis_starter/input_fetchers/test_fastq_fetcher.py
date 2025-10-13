from typing import cast
from unittest.mock import Mock, create_autospec

from housekeeper.store.models import Archive, File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.archive.archive import SpringArchiveAPI
from cg.meta.compress.compress import CompressAPI
from cg.models.compression_data import CaseCompressionData
from cg.services.analysis_starter.input_fetcher.implementations.fastq_fetcher import FastqFetcher
from cg.store.models import Case, Sample
from cg.store.store import Store


def test_ensure_files_are_ready_success():
    # GIVEN a sample and a case in StatusDB
    sample: Sample = create_autospec(Sample)
    case: Case = create_autospec(Case, samples=[sample])
    status_db: Store = create_autospec(Store)
    status_db.get_case_by_internal_id = Mock(return_value=case)

    # GIVEN that the case is not down sampled nor external
    status_db.is_case_down_sampled = Mock(return_value=False)
    status_db.is_case_external = Mock(return_value=False)

    # GIVEN that all Illumina runs are on disk
    status_db.are_all_illumina_runs_on_disk = Mock(return_value=True)

    # GIVEN that there are no files archived via DDN
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    housekeeper_api.get_archived_files_for_bundle = Mock(return_value=[])

    # GIVEN that all spring files are decompressed into FASTQ files
    compress_api: CompressAPI = create_autospec(CompressAPI)
    case_compression_data: CaseCompressionData = create_autospec(CaseCompressionData)
    case_compression_data.is_spring_decompression_needed = Mock(return_value=False)
    case_compression_data.is_spring_decompression_running = Mock(return_value=False)
    compress_api.get_case_compression_data = Mock(return_value=case_compression_data)

    # GIVEN a FastqFetcher
    fastq_fetcher = FastqFetcher(
        compress_api=compress_api,
        housekeeper_api=housekeeper_api,
        spring_archive_api=Mock(),
        status_db=status_db,
    )

    # WHEN ensuring that the files are ready for analysis
    # THEN no error is raised
    fastq_fetcher.ensure_files_are_ready("case_id")


def test_ensure_files_are_ready_archived_spring_files():
    # GIVEN a sample and a case in StatusDB
    sample: Sample = create_autospec(Sample)
    case: Case = create_autospec(Case, samples=[sample])
    status_db: Store = create_autospec(Store)
    status_db.get_case_by_internal_id = Mock(return_value=case)

    # GIVEN that the case is not down sampled nor external
    status_db.is_case_down_sampled = Mock(return_value=False)
    status_db.is_case_external = Mock(return_value=False)

    # GIVEN that all Illumina runs are on disk
    status_db.are_all_illumina_runs_on_disk = Mock(return_value=True)

    # GIVEN that there are no files archived via DDN
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    archive = Archive(file_id=1)
    file = File(id=1, path="path/to/spring_file.spring", archive=archive)
    housekeeper_api.get_archived_files_for_bundle = Mock(return_value=[file])

    # GIVEN that all spring files are decompressed into FASTQ files
    compress_api: CompressAPI = create_autospec(CompressAPI)
    case_compression_data: CaseCompressionData = create_autospec(CaseCompressionData)
    case_compression_data.is_spring_decompression_needed = Mock(return_value=False)
    case_compression_data.is_spring_decompression_running = Mock(return_value=False)
    compress_api.get_case_compression_data = Mock(return_value=case_compression_data)

    spring_archive_api: SpringArchiveAPI = create_autospec(SpringArchiveAPI)

    # GIVEN a FastqFetcher
    fastq_fetcher = FastqFetcher(
        compress_api=compress_api,
        housekeeper_api=housekeeper_api,
        spring_archive_api=spring_archive_api,
        status_db=status_db,
    )

    # WHEN ensuring that the files are ready for analysis
    # THEN no error is raised
    fastq_fetcher.ensure_files_are_ready("case_id")

    cast(Mock, spring_archive_api.retrieve_spring_files_for_case).assert_called_once_with("case_id")
