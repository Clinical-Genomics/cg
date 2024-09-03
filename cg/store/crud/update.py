"""Handler to update data objects"""

from datetime import datetime

from sqlalchemy.orm import Session

from cg.constants import SequencingRunDataAvailability
from cg.constants.constants import SequencingQCStatus
from cg.constants.sequencing import Sequencers
from cg.services.illumina.post_processing.utils import get_q30_threshold
from cg.store.base import BaseHandler
from cg.store.models import (
    Case,
    IlluminaSampleSequencingMetrics,
    IlluminaSequencingRun,
    Order,
    Sample,
)


class UpdateHandler(BaseHandler):
    """Contains methods to update database objects."""

    def __init__(self, session: Session):
        super().__init__(session=session)
        self.session = session

    def update_sample_comment(self, sample_id: int, comment: str) -> None:
        """Update comment on sample with the provided comment."""
        sample: Sample = self.get_sample_by_entry_id(sample_id)
        sample.comment = f"{sample.comment} {comment}" if sample.comment else comment
        self.session.commit()

    def update_order_delivery(self, order_id: int, delivered: bool) -> Order:
        """Update the delivery status of an order."""
        order: Order = self.get_order_by_id(order_id)
        order.is_delivered = delivered
        self.session.commit()
        return order

    def update_illumina_sequencing_run_data_availability(
        self,
        sequencing_run: IlluminaSequencingRun,
        data_availability: SequencingRunDataAvailability,
    ) -> IlluminaSequencingRun:
        """Update the data availability status of an Illumina sequencing run."""
        sequencing_run.data_availability = data_availability
        self.session.commit()
        return sequencing_run

    def update_illumina_sequencing_run_has_backup(
        self, sequencing_run: IlluminaSequencingRun, has_backup: bool
    ) -> IlluminaSequencingRun:
        """Update the backup status of an Illumina sequencing run."""
        sequencing_run.has_backup = has_backup
        self.session.commit()
        return sequencing_run

    def update_sequencing_qc_status(self, case: Case, status: SequencingQCStatus) -> None:
        case.aggregated_sequencing_qc = status
        self.session.commit()

    def update_sample_reads_illumina(self, internal_id: str, sequencer_type: Sequencers):
        sample: Sample = self.get_sample_by_internal_id(internal_id)
        total_reads_for_sample: int = 0
        sample_metrics: list[IlluminaSampleSequencingMetrics] = sample.sample_run_metrics

        q30_threshold: int = get_q30_threshold(sequencer_type)

        for sample_metric in sample_metrics:
            if sample_metric.base_passing_q30_percent >= q30_threshold:
                total_reads_for_sample += sample_metric.total_reads_in_lane

        sample.reads = total_reads_for_sample
        self.session.commit()

    def update_sample_sequenced_at(self, internal_id: str, date: datetime):
        sample: Sample = self.get_sample_by_internal_id(internal_id)
        sample.last_sequenced_at = date
        self.session.commit()

    def mark_sample_as_cancelled(self, sample_id: int) -> None:
        sample: Sample = self.get_sample_by_entry_id(sample_id)
        sample.is_cancelled = True
        self.session.commit()
