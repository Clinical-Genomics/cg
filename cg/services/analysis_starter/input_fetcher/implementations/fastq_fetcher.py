import logging

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.constants import CaseActions
from cg.exc import AnalysisNotReadyError
from cg.meta.archive.archive import SpringArchiveAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.models.cg_config import DataFlowConfig
from cg.services.analysis_starter.input_fetcher.input_fetcher import InputFetcher
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class FastqFetcher(InputFetcher):

    def __init__(
        self,
        status_db: Store,
        housekeeper_api: HousekeeperAPI,
        prepare_fastq_api: PrepareFastqAPI,
        data_flow_config: DataFlowConfig,
    ):
        self.status_db = status_db
        self.housekeeper_api = housekeeper_api
        self.prepare_fastq_api = prepare_fastq_api
        self.data_flow_config = data_flow_config

    def ensure_files_are_ready(self, case_id: str):
        """Retrieves or decompresses Spring files if needed. If so, an AnalysisNotReady error
        is raised."""
        self._ensure_files_are_present(case_id)
        self._resolve_decompression(case_id=case_id, dry_run=False)
        if not self._is_raw_data_ready_for_analysis(case_id):
            raise AnalysisNotReadyError("FASTQ files are not present for the analysis to start")

    def _ensure_files_are_present(self, case_id: str):
        """Checks if any Illumina runs need to be retrieved and submits a job if that is the case.
        Also checks if any spring files are archived and submits a job to retrieve any which are."""
        self._ensure_illumina_run_on_disk(case_id)
        if not self._are_all_spring_files_present(case_id):
            LOG.warning(f"Files are archived for case {case_id}")
            spring_archive_api = SpringArchiveAPI(
                status_db=self.status_db,
                housekeeper_api=self.housekeeper_api,
                data_flow_config=self.data_flow_config,
            )
            spring_archive_api.retrieve_spring_files_for_case(case_id)

    def _ensure_illumina_run_on_disk(self, case_id: str) -> None:
        """Check if Illumina sequencing runs are on disk for given case."""
        if not self._is_illumina_run_check_applicable(case_id):
            LOG.info(
                "Illumina run check is not applicable - "
                "the case is either down sampled or external."
            )
            return
        if not self.status_db.are_all_illumina_runs_on_disk(case_id):
            self.status_db.request_sequencing_runs_for_case(case_id)

    def _are_all_spring_files_present(self, case_id: str) -> bool:
        """Return True if no Spring files for the case are archived in the data location used by the customer."""
        case: Case = self.status_db.get_case_by_internal_id(case_id)
        for sample in case.samples:
            if (
                files := self.housekeeper_api.get_archived_files_for_bundle(
                    bundle_name=sample.internal_id, tags=[SequencingFileTag.SPRING]
                )
            ) and not all(file.archive.retrieved_at for file in files):
                return False
        return True

    def _resolve_decompression(self, case_id: str, dry_run: bool) -> None:
        """
        Decompresses a case if needed and adds new fastq files to Housekeeper.
        """
        if self.prepare_fastq_api.is_spring_decompression_needed(case_id):
            self._decompress_case(case_id=case_id, dry_run=dry_run)
            return

        if self.prepare_fastq_api.is_spring_decompression_running(case_id):
            self.status_db.set_case_action(case_internal_id=case_id, action=CaseActions.ANALYZE)
            return

        self.prepare_fastq_api.add_decompressed_fastq_files_to_housekeeper(case_id)

    def _decompress_case(self, case_id: str, dry_run: bool) -> None:
        """Decompress all possible fastq files for all samples in a case"""

        # Very messy due to dry run
        LOG.info(f"The analysis for {case_id} could not start, decompression is needed")
        is_decompression_possible: bool = (
            self.prepare_fastq_api.can_at_least_one_sample_be_decompressed(case_id)
        )
        if not is_decompression_possible:
            # Raise error? This is messy
            self._set_to_analyze_if_decompressing(case_id)
            return
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        any_decompression_started = False
        for sample in case.samples:
            sample_id: str = sample.internal_id
            if dry_run:
                LOG.info(
                    f"This is a dry run, therefore decompression for {sample_id} won't be started"
                )
                continue
            decompression_started: bool = self.prepare_fastq_api.compress_api.decompress_spring(
                sample_id
            )
            if decompression_started:
                any_decompression_started = True

        if not any_decompression_started:
            # Raise error?
            LOG.warning(f"Decompression failed to start for {case_id}")
            return
        if not dry_run:
            self.status_db.set_case_action(case_internal_id=case_id, action=CaseActions.ANALYZE)
        LOG.info(f"Decompression started for {case_id}")

    def _is_raw_data_ready_for_analysis(self, case_id: str) -> bool:
        """Returns True if no files need to be retrieved from an external location and if all Spring files are
        decompressed."""

        # Should this reference spring files? No need to be vague in the fastq fetcher
        if self._does_any_file_need_to_be_retrieved(case_id):
            return False
        if self.prepare_fastq_api.is_spring_decompression_needed(
            case_id
        ) or self.prepare_fastq_api.is_spring_decompression_running(case_id):
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

    def _set_to_analyze_if_decompressing(self, case_id: str) -> None:
        """Sets a case's action to 'analyze' if it is currently being decompressed."""
        is_decompression_running: bool = self.prepare_fastq_api.is_spring_decompression_running(
            case_id
        )
        if not is_decompression_running:
            # Raise error?
            LOG.warning(f"Decompression can not be started for {case_id}")
            return
        LOG.info(
            f"Decompression is running for {case_id}, analysis will be started when decompression is done"
        )
        self.status_db.set_case_action(case_internal_id=case_id, action=CaseActions.ANALYZE)
