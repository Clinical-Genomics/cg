import logging
from pathlib import Path

from housekeeper.store.models import File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.constants import PIPELINES_USING_PARTIAL_ANALYSES, CaseActions
from cg.exc import AnalysisNotReadyError, DecompressionCouldNotStartError
from cg.meta.archive.archive import SpringArchiveAPI
from cg.meta.compress import CompressAPI, files
from cg.models.compression_data import CaseCompressionData, CompressionData, SampleCompressionData
from cg.services.analysis_starter.input_fetcher.input_fetcher import InputFetcher
from cg.store.models import Case, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class FastqFetcher(InputFetcher):

    def __init__(
        self,
        compress_api: CompressAPI,
        housekeeper_api: HousekeeperAPI,
        spring_archive_api: SpringArchiveAPI,
        status_db: Store,
    ):
        self.status_db = status_db
        self.housekeeper_api = housekeeper_api
        self.compress_api = compress_api
        self.spring_archive_api = spring_archive_api

    def ensure_files_are_ready(self, case_id: str) -> None:
        """
        Ensures FASTQ files are ready to be analysed. Executes the following processes if needed:
        1. Retrieval of flow cells via PDC.
        2. Retrieval of Spring files via DDN.
        3. Decompression of Spring files.
        4. Adds decompressed FASTQ files to Housekeeper.
        Raises:
            AnalysisNotReadyError if the FASTQ files are not ready to be analysed.
        """
        self._ensure_files_are_present(case_id)
        self._resolve_decompression(case_id)
        if not self._are_fastq_files_ready_for_analysis(case_id):
            raise AnalysisNotReadyError(
                f"FASTQ files needed to start case {case_id} are not present"
            )
        LOG.info(f"All FASTQ files are ready for analysing case {case_id}")

    def _ensure_files_are_present(self, case_id: str) -> None:
        """Checks if any Illumina runs need to be retrieved and queries PDC if that is the case.
        Also checks if any spring files are archived and submits a job to retrieve any which are."""
        self._ensure_illumina_run_on_disk(case_id)
        if not self._are_all_spring_files_present(case_id):
            LOG.warning(f"Files are archived for case {case_id}")
            self.spring_archive_api.retrieve_spring_files_for_case(case_id)

    def _ensure_illumina_run_on_disk(self, case_id: str) -> None:
        """Check if Illumina sequencing runs are on disk for given case. Downsampled and external
        cases are disregarded."""
        if not self._is_illumina_run_check_applicable(case_id):
            LOG.info(
                "Illumina run check is not applicable - "
                "the case is either down sampled or external."
            )
            return
        if not self.status_db.are_all_illumina_runs_on_disk(case_id):
            self.status_db.request_sequencing_runs_for_case(case_id)

    def _are_all_spring_files_present(self, case_id: str) -> bool:
        """Return True if no Spring files for the case are archived."""
        case: Case = self.status_db.get_case_by_internal_id(case_id)
        for sample in case.samples:
            if (
                files := self.housekeeper_api.get_archived_files_for_bundle(
                    bundle_name=sample.internal_id, tags=[SequencingFileTag.SPRING]
                )
            ) and not all(file.archive.retrieved_at for file in files):
                return False
        return True

    def _resolve_decompression(self, case_id: str) -> None:
        """
        Decompresses a case if needed and adds new fastq files to Housekeeper.
        """
        case: Case = self.status_db.get_case_by_internal_id(case_id)
        case_compression_data: CaseCompressionData = self.compress_api.get_case_compression_data(
            case
        )
        if case_compression_data.is_spring_decompression_needed():
            LOG.info(f"The analysis for {case_id} could not start, decompression is needed")
            if not case_compression_data.can_at_least_one_sample_be_decompressed():
                self._set_to_analyze_if_decompressing(case_compression_data)
            else:
                self._decompress_case(case_id)
        elif case_compression_data.is_spring_decompression_running():
            self.status_db.update_case_action(case_internal_id=case_id, action=CaseActions.ANALYZE)
            return

        self._add_decompressed_fastq_files_to_housekeeper(case_id)

    def _decompress_case(self, case_id: str) -> None:
        """Decompress all possible fastq files for all samples in a case"""
        case: Case = self.status_db.get_case_by_internal_id(case_id)
        try:
            self.compress_api.decompress_case(case)
        except DecompressionCouldNotStartError:
            LOG.warning(f"Decompression failed to start for {case_id}")
            return
        self.status_db.update_case_action(case_internal_id=case_id, action=CaseActions.ANALYZE)
        LOG.info(f"Decompression started for {case_id}")

    def _are_fastq_files_ready_for_analysis(self, case_id: str) -> bool:
        """Returns True if no files need to be retrieved from an external location and if all Spring files are
        decompressed."""
        case: Case = self.status_db.get_case_by_internal_id(case_id)
        case_compression_data: CaseCompressionData = self.compress_api.get_case_compression_data(
            case
        )
        if self._does_any_file_need_to_be_retrieved(case_id):
            return False
        if (
            case_compression_data.is_spring_decompression_needed()
            or case_compression_data.is_spring_decompression_running()
        ):
            LOG.warning(f"Case {case_id} is not ready - not all files are decompressed.")
            return False
        return True

    def _does_any_file_need_to_be_retrieved(self, case_id: str) -> bool:
        """Checks whether we need to retrieve files from an external data location."""
        if self._is_illumina_run_check_applicable(
            case_id
        ) and not self.status_db.are_all_illumina_runs_on_disk(case_id):
            LOG.warning(f"Case {case_id} is not ready - not all Illumina runs present on disk.")
            return True
        else:
            if not self._are_all_spring_files_present(case_id):
                LOG.warning(f"Case {case_id} is not ready - some files are archived.")
                return True
        return False

    def _is_illumina_run_check_applicable(self, case_id) -> bool:
        """Returns true if the case is neither down sampled nor external."""
        return not (
            self.status_db.is_case_down_sampled(case_id) or self.status_db.is_case_external(case_id)
        )

    def _set_to_analyze_if_decompressing(self, case_compression_data: CaseCompressionData) -> None:
        """Sets a case's action to 'analyze' if it is currently being decompressed."""
        case_id: str = case_compression_data.case_id
        if case_compression_data.is_spring_decompression_running():
            LOG.info(
                f"Decompression is running for {case_id}, analysis will be started when decompression is done"
            )
            self.status_db.update_case_action(case_internal_id=case_id, action=CaseActions.ANALYZE)

    @staticmethod
    def _should_skip_sample(case: Case, sample: Sample) -> bool:
        """
        For some workflows, we want to start a partial analysis disregarding the samples with no reads.
        This method returns true if we should skip the sample.
        """
        return case.data_analysis in PIPELINES_USING_PARTIAL_ANALYSES and not sample.has_reads

    def _add_decompressed_fastq_files_to_housekeeper(self, case_id: str) -> None:
        """Adds decompressed FASTQ files to Housekeeper for a case, if there are any."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        for sample in case.samples:
            if self._should_skip_sample(case=case, sample=sample):
                LOG.warning(f"Skipping sample {sample.internal_id} - it has no reads.")
                continue
            self._add_decompressed_sample(sample=sample)

    def _add_decompressed_sample(self, sample: Sample) -> None:
        """Adds decompressed FASTQ files to Housekeeper for a sample, if there are any."""
        sample_id = sample.internal_id
        compression_data: SampleCompressionData = self.compress_api.get_sample_compression_data(
            sample_id
        )
        if not self._are_all_fastqs_in_housekeeper(compression_data):
            self.compress_api.add_decompressed_fastq(sample)

    def _are_all_fastqs_in_housekeeper(
        self, sample_compression_data: SampleCompressionData
    ) -> bool:
        """Returns true if all Spring files are decompressed for the sample."""
        sample_id: str = sample_compression_data.sample_id
        version: Version = self.housekeeper_api.get_latest_bundle_version(sample_id)
        fastq_files = files.get_hk_files_dict(tags=[SequencingFileTag.FASTQ], version_obj=version)
        return all(
            self._is_fastq_pair_in_housekeeper(compression=compression, fastq_files=fastq_files)
            for compression in sample_compression_data.compression_objects
        )

    @staticmethod
    def _is_fastq_pair_in_housekeeper(
        compression: CompressionData, fastq_files: dict[Path, File]
    ) -> bool:
        return compression.fastq_first in fastq_files and compression.fastq_second in fastq_files
