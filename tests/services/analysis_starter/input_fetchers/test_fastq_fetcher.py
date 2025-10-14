from unittest.mock import Mock, create_autospec

import pytest
from housekeeper.store.models import Archive, File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import CaseActions
from cg.exc import AnalysisNotReadyError
from cg.meta.archive.archive import SpringArchiveAPI
from cg.meta.compress.compress import CompressAPI
from cg.models.compression_data import CaseCompressionData
from cg.services.analysis_starter.input_fetcher.implementations.fastq_fetcher import FastqFetcher
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


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

    # GIVEN that there is a file archived via DDN
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    archive = Archive(file_id=1)
    file = File(id=1, path="path/to/spring_file.spring", archive=archive)
    housekeeper_api.get_archived_files_for_bundle = Mock(return_value=[file])

    # GIVEN that all spring files on the cluster are decompressed into FASTQ files
    compress_api: CompressAPI = create_autospec(CompressAPI)
    case_compression_data: CaseCompressionData = create_autospec(CaseCompressionData)
    case_compression_data.is_spring_decompression_needed = Mock(return_value=False)
    case_compression_data.is_spring_decompression_running = Mock(return_value=False)
    compress_api.get_case_compression_data = Mock(return_value=case_compression_data)

    # GIVEN the spring archive API can be used
    spring_archive_api: TypedMock[SpringArchiveAPI] = create_typed_mock(SpringArchiveAPI)

    # GIVEN a FastqFetcher
    fastq_fetcher = FastqFetcher(
        compress_api=compress_api,
        housekeeper_api=housekeeper_api,
        spring_archive_api=spring_archive_api.as_type,
        status_db=status_db,
    )

    # WHEN ensuring that the files are ready for analysis
    # THEN an error is raised
    with pytest.raises(AnalysisNotReadyError):
        fastq_fetcher.ensure_files_are_ready("case_id")

    # THEN the Spring files for the case should have started to be retrieved
    spring_archive_api.as_mock.retrieve_spring_files_for_case.assert_called_once_with("case_id")


def test_ensure_files_are_ready_fetch_flow_cell():
    # GIVEN a sample and a case in StatusDB
    sample: Sample = create_autospec(Sample)
    case: Case = create_autospec(Case, samples=[sample])
    status_db: TypedMock[Store] = create_typed_mock(Store)
    status_db.as_type.get_case_by_internal_id = Mock(return_value=case)

    # GIVEN that the case is not down sampled nor external
    status_db.as_type.is_case_down_sampled = Mock(return_value=False)
    status_db.as_type.is_case_external = Mock(return_value=False)

    # GIVEN that not all Illumina runs are on disk
    status_db.as_type.are_all_illumina_runs_on_disk = Mock(return_value=False)

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
        status_db=status_db.as_type,
    )

    # WHEN ensuring that the files are ready for analysis
    # THEN an AnalysisNotReadyError is raised
    with pytest.raises(AnalysisNotReadyError):
        fastq_fetcher.ensure_files_are_ready("case_id")

    # THEN the flow cells for the case should have been requested
    status_db.as_mock.request_sequencing_runs_for_case.assert_called_once_with("case_id")


@pytest.mark.parametrize(
    "is_downsampled, is_external", [(False, True), (True, False), (True, True)]
)
def test_ensure_files_are_ready_down_sampled_or_external(is_downsampled: bool, is_external: bool):
    # GIVEN a sample and a case in StatusDB
    sample: Sample = create_autospec(Sample)
    case: Case = create_autospec(Case, samples=[sample])
    status_db: TypedMock[Store] = create_typed_mock(Store)
    status_db.as_type.get_case_by_internal_id = Mock(return_value=case)

    # GIVEN that the case is either down sampled and/or external so no flow cells are found in StatusDB
    status_db.as_type.is_case_down_sampled = Mock(return_value=is_downsampled)
    status_db.as_type.is_case_external = Mock(return_value=is_external)
    status_db.as_type.are_all_illumina_runs_on_disk = Mock(return_value=False)

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
        status_db=status_db.as_type,
    )

    # WHEN ensuring that the files are ready for analysis
    # THEN the files should be ready for analysis
    fastq_fetcher.ensure_files_are_ready("case_id")


def test_ensure_files_are_ready_decompression_needed():
    # GIVEN a sample and a case in StatusDB
    sample: Sample = create_autospec(Sample)
    case: Case = create_autospec(Case, samples=[sample])
    status_db: TypedMock[Store] = create_typed_mock(Store)
    status_db.as_type.get_case_by_internal_id = Mock(return_value=case)

    # GIVEN that the case is not down sampled nor external
    status_db.as_type.is_case_down_sampled = Mock(return_value=False)
    status_db.as_type.is_case_external = Mock(return_value=False)

    # GIVEN that all Illumina runs are on disk
    status_db.as_type.are_all_illumina_runs_on_disk = Mock(return_value=True)

    # GIVEN that there are no files archived via DDN
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    housekeeper_api.get_archived_files_for_bundle = Mock(return_value=[])

    # GIVEN that some spring files need to be decompressed into FASTQ files
    compress_api: TypedMock[CompressAPI] = create_typed_mock(CompressAPI)
    case_compression_data: CaseCompressionData = create_autospec(CaseCompressionData)
    case_compression_data.is_spring_decompression_needed = Mock(return_value=True)
    case_compression_data.is_spring_decompression_running = Mock(return_value=False)
    case_compression_data.can_at_least_one_sample_be_decompressed = Mock(return_value=True)
    compress_api.as_type.get_case_compression_data = Mock(return_value=case_compression_data)

    # GIVEN a FastqFetcher
    fastq_fetcher = FastqFetcher(
        compress_api=compress_api.as_type,
        housekeeper_api=housekeeper_api,
        spring_archive_api=Mock(),
        status_db=status_db.as_type,
    )

    # WHEN ensuring that the files are ready for analysis
    # THEN an AnalysisNotReadyError is raised
    with pytest.raises(AnalysisNotReadyError):
        fastq_fetcher.ensure_files_are_ready("case_id")

    # THEN decompression should have been started
    compress_api.as_mock.decompress_case.assert_called_once_with(case)

    # THEN the case should have been set to analyze
    status_db.as_mock.update_case_action.assert_called_once_with(
        case_internal_id="case_id", action=CaseActions.ANALYZE
    )


def test_ensure_files_are_ready_decompression_needed_but_no_samples_can_be_decompressed_and_decompression_is_already_running():
    # GIVEN a sample and a case in StatusDB
    sample: Sample = create_autospec(Sample)
    case: Case = create_autospec(Case, samples=[sample])
    status_db: TypedMock[Store] = create_typed_mock(Store)
    status_db.as_type.get_case_by_internal_id = Mock(return_value=case)

    # GIVEN that the case is not down sampled nor external
    status_db.as_type.is_case_down_sampled = Mock(return_value=False)
    status_db.as_type.is_case_external = Mock(return_value=False)

    # GIVEN that all Illumina runs are on disk
    status_db.as_type.are_all_illumina_runs_on_disk = Mock(return_value=True)

    # GIVEN that there are no files archived via DDN
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    housekeeper_api.get_archived_files_for_bundle = Mock(return_value=[])

    # GIVEN that some spring files need to be decompressed into FASTQ files
    compress_api: TypedMock[CompressAPI] = create_typed_mock(CompressAPI)
    case_compression_data: CaseCompressionData = create_autospec(
        CaseCompressionData, case_id="case_id"
    )
    case_compression_data.is_spring_decompression_needed = Mock(return_value=True)

    # GIVEN that no samples can be decompressed
    case_compression_data.can_at_least_one_sample_be_decompressed = Mock(return_value=False)

    # GIVEN that decompression is running
    case_compression_data.is_spring_decompression_running = Mock(return_value=True)

    compress_api.as_type.get_case_compression_data = Mock(return_value=case_compression_data)

    # GIVEN a FastqFetcher
    fastq_fetcher = FastqFetcher(
        compress_api=compress_api.as_type,
        housekeeper_api=housekeeper_api,
        spring_archive_api=Mock(),
        status_db=status_db.as_type,
    )

    # WHEN ensuring that the files are ready for analysis
    # THEN an AnalysisNotReadyError is raised
    with pytest.raises(AnalysisNotReadyError):
        fastq_fetcher.ensure_files_are_ready("case_id")

    # THEN the case should have been set to analyze
    status_db.as_mock.update_case_action.assert_called_once_with(
        case_internal_id="case_id", action=CaseActions.ANALYZE
    )


def test_ensure_files_are_ready_decompression_needed_but_no_samples_can_be_decompressed_and_decompression_is_not_already_running():
    # GIVEN a sample and a case in StatusDB
    sample: Sample = create_autospec(Sample)
    case: Case = create_autospec(Case, samples=[sample])
    status_db: TypedMock[Store] = create_typed_mock(Store)
    status_db.as_type.get_case_by_internal_id = Mock(return_value=case)

    # GIVEN that the case is not down sampled nor external
    status_db.as_type.is_case_down_sampled = Mock(return_value=False)
    status_db.as_type.is_case_external = Mock(return_value=False)

    # GIVEN that all Illumina runs are on disk
    status_db.as_type.are_all_illumina_runs_on_disk = Mock(return_value=True)

    # GIVEN that there are no files archived via DDN
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    housekeeper_api.get_archived_files_for_bundle = Mock(return_value=[])

    # GIVEN that some spring files need to be decompressed into FASTQ files
    compress_api: TypedMock[CompressAPI] = create_typed_mock(CompressAPI)
    case_compression_data: CaseCompressionData = create_autospec(
        CaseCompressionData, case_id="case_id"
    )
    case_compression_data.is_spring_decompression_needed = Mock(return_value=True)

    # GIVEN that no samples can be decompressed
    case_compression_data.can_at_least_one_sample_be_decompressed = Mock(return_value=False)

    # GIVEN that decompression is not running
    case_compression_data.is_spring_decompression_running = Mock(return_value=False)

    compress_api.as_type.get_case_compression_data = Mock(return_value=case_compression_data)

    # GIVEN a FastqFetcher
    fastq_fetcher = FastqFetcher(
        compress_api=compress_api.as_type,
        housekeeper_api=housekeeper_api,
        spring_archive_api=Mock(),
        status_db=status_db.as_type,
    )

    # WHEN ensuring that the files are ready for analysis
    # THEN an AnalysisNotReadyError is raised
    with pytest.raises(AnalysisNotReadyError):
        fastq_fetcher.ensure_files_are_ready("case_id")

    # THEN the case should not have been set to analyze
    assert not status_db.as_mock.update_case_action.called


def test_ensure_files_are_ready_decompression_running():
    # GIVEN a sample and a case in StatusDB
    sample: Sample = create_autospec(Sample)
    case: Case = create_autospec(Case, samples=[sample])
    status_db: TypedMock[Store] = create_typed_mock(Store)
    status_db.as_type.get_case_by_internal_id = Mock(return_value=case)

    # GIVEN that the case is not down sampled nor external
    status_db.as_type.is_case_down_sampled = Mock(return_value=False)
    status_db.as_type.is_case_external = Mock(return_value=False)

    # GIVEN that all Illumina runs are on disk
    status_db.as_type.are_all_illumina_runs_on_disk = Mock(return_value=True)

    # GIVEN that there are no files archived via DDN
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    housekeeper_api.get_archived_files_for_bundle = Mock(return_value=[])

    # GIVEN that some spring files are currently being decompressed into FASTQ files
    compress_api: TypedMock[CompressAPI] = create_typed_mock(CompressAPI)
    case_compression_data: CaseCompressionData = create_autospec(CaseCompressionData)
    case_compression_data.is_spring_decompression_needed = Mock(return_value=False)
    case_compression_data.is_spring_decompression_running = Mock(return_value=True)
    compress_api.as_type.get_case_compression_data = Mock(return_value=case_compression_data)

    # GIVEN a FastqFetcher
    fastq_fetcher = FastqFetcher(
        compress_api=compress_api.as_type,
        housekeeper_api=housekeeper_api,
        spring_archive_api=Mock(),
        status_db=status_db.as_type,
    )

    # WHEN ensuring that the files are ready for analysis
    # THEN an AnalysisNotReadyError is raised
    with pytest.raises(AnalysisNotReadyError):
        fastq_fetcher.ensure_files_are_ready("case_id")

    # THEN the case should have been set to analyze
    status_db.as_mock.update_case_action.assert_called_once_with(
        case_internal_id="case_id", action=CaseActions.ANALYZE
    )
