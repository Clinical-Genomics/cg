"""Handler to update data objects."""

from datetime import datetime

from cg.constants import SequencingRunDataAvailability
from cg.constants.constants import CaseActions, SequencingQCStatus
from cg.constants.sequencing import Sequencers
from cg.services.illumina.post_processing.utils import get_q30_threshold
from cg.store.crud.read import ReadHandler
from cg.store.models import (
    Analysis,
    Case,
    IlluminaSampleSequencingMetrics,
    IlluminaSequencingRun,
    Order,
    Sample,
)


class UpdateMixin(ReadHandler):
    """Contains methods to update database objects."""

    def update_sample_comment(self, sample_id: int, comment: str) -> None:
        """Update comment on sample with the provided comment."""
        sample: Sample = self.get_sample_by_entry_id(sample_id)
        sample.comment = f"{sample.comment} {comment}" if sample.comment else comment
        self.commit_to_store()

    def update_order_status(self, order_id: int, open: bool) -> Order:
        """Update the status of an order."""
        order: Order = self.get_order_by_id(order_id)
        order.is_open = open
        self.commit_to_store()
        return order

    def update_illumina_sequencing_run_data_availability(
        self,
        sequencing_run: IlluminaSequencingRun,
        data_availability: SequencingRunDataAvailability,
    ) -> IlluminaSequencingRun:
        """Update the data availability status of an Illumina sequencing run."""
        sequencing_run.data_availability = data_availability
        self.commit_to_store()
        return sequencing_run

    def update_illumina_sequencing_run_has_backup(
        self, sequencing_run: IlluminaSequencingRun, has_backup: bool
    ) -> IlluminaSequencingRun:
        """Update the backup status of an Illumina sequencing run."""
        sequencing_run.has_backup = has_backup
        self.commit_to_store()
        return sequencing_run

    def update_sequencing_qc_status(self, case: Case, status: SequencingQCStatus) -> None:
        case.aggregated_sequencing_qc = status
        self.commit_to_store()

    def update_case_action(self, action: CaseActions | None, case_internal_id: str) -> None:
        """Sets the action of the provided case the given action (can be None)."""
        case: Case = self.get_case_by_internal_id(internal_id=case_internal_id)
        case.action = action
        self.commit_to_store()

    def update_sample_reads_illumina(self, internal_id: str, sequencer_type: Sequencers):
        sample: Sample = self.get_sample_by_internal_id(internal_id)
        total_reads_for_sample: int = 0
        sample_metrics: list[IlluminaSampleSequencingMetrics] = sample.sample_run_metrics

        q30_threshold: int = get_q30_threshold(sequencer_type)

        for sample_metric in sample_metrics:
            if (
                sample_metric.base_passing_q30_percent >= q30_threshold
                or sample.is_negative_control
            ):
                total_reads_for_sample += sample_metric.total_reads_in_lane

        sample.reads = total_reads_for_sample
        self.commit_to_store()

    def update_sample_reads(self, internal_id: str, reads: int):
        """Add reads to the current reads for a sample."""
        sample: Sample = self.get_sample_by_internal_id(internal_id)
        sample.reads += reads
        self.commit_to_store()

    def update_sample_sequenced_at(self, internal_id: str, date: datetime):
        sample: Sample = self.get_sample_by_internal_id(internal_id)
        sample.last_sequenced_at = date
        self.commit_to_store()

    def mark_sample_as_cancelled(self, sample_id: int) -> None:
        sample: Sample = self.get_sample_by_entry_id(sample_id)
        sample.is_cancelled = True
        self.commit_to_store()

    def update_analysis_completed_at(self, analysis_id: int, completed_at: datetime | None) -> None:
        analysis: Analysis = self.get_analysis_by_entry_id(analysis_id)
        analysis.completed_at = completed_at
        self.commit_to_store()

    def update_analysis_housekeeper_version_id(self, analysis_id: int, version_id: int) -> None:
        """Update the Housekeeper version ID of an analysis."""
        analysis: Analysis = self.get_analysis_by_entry_id(analysis_id)
        analysis.housekeeper_version_id = version_id
        self.commit_to_store()

    def update_analysis_comment(self, analysis_id: int, comment: str | None) -> None:
        """Update the comment field of an analysis appending the new comment over any existing."""
        analysis: Analysis = self.get_analysis_by_entry_id(analysis_id)
        analysis.comment = f"{analysis.comment}\n{comment}" if analysis.comment else comment
        self.commit_to_store()

    def update_analysis_uploaded_at(self, analysis_id: int, uploaded_at: datetime | None) -> None:
        """Update the uploaded at field of an analysis."""
        analysis: Analysis = self.get_analysis_by_entry_id(analysis_id)
        analysis.uploaded_at = uploaded_at
        self.commit_to_store()

    def update_analysis_upload_started_at(
        self, analysis_id: int, upload_started_at: datetime | None
    ) -> None:
        """Update the upload started at field of an analysis."""
        analysis: Analysis = self.get_analysis_by_entry_id(analysis_id)
        analysis.upload_started_at = upload_started_at
        self.commit_to_store()

    def update_analysis_delivery_report_date(
        self, analysis_id: int, delivery_report_date: datetime | None
    ) -> None:
        """Update the delivery report created_at field of an analysis."""
        analysis: Analysis = self.get_analysis_by_entry_id(analysis_id)
        analysis.delivery_report_created_at = delivery_report_date
        self.commit_to_store()
