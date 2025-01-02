import logging
from pathlib import Path

from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Priority, Workflow
from cg.constants.tb import AnalysisType
from cg.meta.workflow.utils.utils import MAP_TO_TRAILBLAZER_PRIORITY
from cg.services.analysis_service.analysis_service import AnalysisService
from cg.services.deliver_files.deliver_files_service.error_handling import (
    handle_no_delivery_files_error,
)
from cg.services.deliver_files.file_fetcher.abstract import FetchDeliveryFilesService
from cg.services.deliver_files.file_fetcher.models import DeliveryFiles
from cg.services.deliver_files.file_formatter.destination.abstract import (
    DeliveryDestinationFormatter,
)
from cg.services.deliver_files.file_formatter.destination.models import FormattedFiles
from cg.services.deliver_files.file_mover.abstract import DestinationFilesMover
from cg.services.deliver_files.rsync.service import DeliveryRsyncService
from cg.store.exc import EntryNotFoundError
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class DeliverFilesService:
    """
    Deliver files for a case, cases in a ticket or a sample to a specified destination or upload location.
    Requires:
        - FetchDeliveryFilesService: Service to fetch the files to deliver from housekeeper
        - DestinationFilesMover: Service to move the files to the destination of delivery or upload
        - DeliveryDestinationFormatter: Service to format the files to the destination format
        - DeliveryRsyncService: Service to run rsync for the delivery
        - TrailblazerAPI: Service to interact with Trailblazer
        - AnalysisService: Service to interact with the analysis
        - Store: Store to interact with the database
    """

    def __init__(
        self,
        delivery_file_manager_service: FetchDeliveryFilesService,
        move_file_service: DestinationFilesMover,
        file_formatter_service: DeliveryDestinationFormatter,
        rsync_service: DeliveryRsyncService,
        tb_service: TrailblazerAPI,
        analysis_service: AnalysisService,
        status_db: Store,
    ):
        self.file_manager = delivery_file_manager_service
        self.file_mover = move_file_service
        self.file_formatter = file_formatter_service
        self.status_db = status_db
        self.rsync_service = rsync_service
        self.tb_service = tb_service
        self.analysis_service = analysis_service

    @handle_no_delivery_files_error
    def deliver_files_for_case(
        self, case: Case, delivery_base_path: Path, dry_run: bool = False
    ) -> None:
        """Deliver the files for a case to the customer folder.
        args:
            case: The case to deliver files for
            delivery_base_path: The base path to deliver the files to
            dry_run: Whether to perform a dry run or not
        """
        delivery_files: DeliveryFiles = self.file_manager.get_files_to_deliver(
            case_id=case.internal_id
        )
        moved_files: DeliveryFiles = self.file_mover.move_files(
            delivery_files=delivery_files, delivery_base_path=delivery_base_path
        )
        formatted_files: FormattedFiles = self.file_formatter.format_files(
            delivery_files=moved_files
        )

        folders_to_deliver: set[Path] = set(
            [formatted_file.formatted_path.parent for formatted_file in formatted_files.files]
        )
        job_id: int = self._start_rsync_job(
            case=case, dry_run=dry_run, folders_to_deliver=folders_to_deliver
        )
        self._add_trailblazer_tracking(case=case, job_id=job_id, dry_run=dry_run)

    def deliver_files_for_ticket(
        self, ticket_id: str, delivery_base_path: Path, dry_run: bool = False
    ) -> None:
        """Deliver the files for all cases in a ticket to the customer folder.
        args:
            ticket_id: The ticket id to deliver files for
            delivery_base_path: The base path to deliver the files to
            dry_run: Whether to perform a dry run or not
        """
        cases: list[Case] = self.status_db.get_cases_by_ticket_id(ticket_id)
        if not cases:
            raise EntryNotFoundError(f"No cases found for ticket {ticket_id}")
        for case in cases:
            self.deliver_files_for_case(
                case=case, delivery_base_path=delivery_base_path, dry_run=dry_run
            )

    def deliver_files_for_sample(
        self, case: Case, sample_id: str, delivery_base_path: Path, dry_run: bool = False
    ):
        """Deliver the files for a sample to the customer folder."""
        delivery_files: DeliveryFiles = self.file_manager.get_files_to_deliver(
            case_id=case.internal_id, sample_id=sample_id
        )
        moved_files: DeliveryFiles = self.file_mover.move_files(
            delivery_files=delivery_files, delivery_base_path=delivery_base_path
        )
        formatted_files: FormattedFiles = self.file_formatter.format_files(
            delivery_files=moved_files
        )
        folders_to_deliver: set[Path] = set(
            [formatted_file.formatted_path.parent for formatted_file in formatted_files.files]
        )
        job_id: int = self._start_rsync_job(
            case=case, dry_run=dry_run, folders_to_deliver=folders_to_deliver
        )
        self._add_trailblazer_tracking(case=case, job_id=job_id, dry_run=dry_run)

    def deliver_files_for_sample_no_rsync(
        self, case: Case, sample_id: str, delivery_base_path: Path
    ):
        """
        Deliver the files for a sample to the delivery base path. Does not perform rsync.
        args:
            case: The case to deliver files for
            sample_id: The sample to deliver files for
            delivery_base_path: The base path to deliver the files to
        """
        delivery_files: DeliveryFiles = self.file_manager.get_files_to_deliver(
            case_id=case.internal_id, sample_id=sample_id
        )
        moved_files: DeliveryFiles = self.file_mover.move_files(
            delivery_files=delivery_files, delivery_base_path=delivery_base_path
        )
        self.file_formatter.format_files(delivery_files=moved_files)

    def _start_rsync_job(self, case: Case, dry_run: bool, folders_to_deliver: set[Path]) -> int:
        """Start a rsync job for the case.
        args:
            case: The case to start the rsync job for
            dry_run: Whether to perform a dry run or not
            folders_to_deliver: The folders to deliver
        """
        LOG.debug(f"[RSYNC] Starting rsync job for case {case.internal_id}")
        job_id: int = self.rsync_service.run_rsync_for_case(
            case=case,
            dry_run=dry_run,
            folders_to_deliver=folders_to_deliver,
        )
        self.rsync_service.write_trailblazer_config(
            content={"jobs": [str(job_id)]},
            config_path=self.rsync_service.trailblazer_config_path,
            dry_run=dry_run,
        )
        return job_id

    def _add_trailblazer_tracking(self, case: Case, job_id: int, dry_run: bool) -> None:
        """Add the rsync job to Trailblazer for tracking.
        args:
            case: The case to add the job for
            job_id: The job id to add for trailblazer tracking
            dry_run: Whether to perform a dry run or not
        """
        if dry_run:
            LOG.info(f"Would have added the analysis for case {case.internal_id} to Trailblazer")
        else:
            LOG.debug(f"[TB SERVICE] Adding analysis for case {case.internal_id} to Trailblazer")
            analysis: TrailblazerAnalysis = self.tb_service.add_pending_analysis(
                case_id=f"{case.internal_id}_rsync",
                analysis_type=AnalysisType.OTHER,
                config_path=self.rsync_service.trailblazer_config_path.as_posix(),
                order_id=case.latest_order.id,
                out_dir=self.rsync_service.log_dir.as_posix(),
                priority=MAP_TO_TRAILBLAZER_PRIORITY[case.priority],
                workflow=Workflow.RSYNC,
                ticket=case.latest_ticket,
            )
            self.tb_service.add_upload_job_to_analysis(analysis_id=analysis.id, slurm_id=job_id)
            self.analysis_service.add_upload_job(slurm_id=job_id, case_id=case.internal_id)
            LOG.info(f"Transfer of case {case.internal_id} started with SLURM job id {job_id}")
