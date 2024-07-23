"""Handler to update data objects"""

from datetime import datetime

from sqlalchemy.orm import Session


from cg.constants import SequencingRunDataAvailability
from cg.store.base import BaseHandler
from cg.store.models import IlluminaSequencingRun, IlluminaSampleSequencingMetrics, SampleRunMetrics

from cg.constants.constants import SequencingQCStatus
from cg.store.base import BaseHandler
from cg.store.models import Case, Order, Sample


class UpdateHandler(BaseHandler):
    """Contains methods to update database objects."""

    def __init__(self, session: Session):
        super().__init__(session=session)
        self.session = session

    def update_sample_comment(self, sample: Sample, comment: str) -> None:
        """Update comment on sample with the provided comment."""
        if sample.comment:
            sample.comment = sample.comment + " " + comment
        else:
            sample.comment = comment
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

    def update_sample_reads_illumina(self, internal_id: str):
        sample: Sample = self.get_sample_by_internal_id(internal_id)
        total_reads_for_sample: int = 0
        sample_metrics: list[IlluminaSampleSequencingMetrics] = sample.sample_run_metrics
        for sample_metric in sample_metrics:
            total_reads_for_sample += sample_metric.total_reads_in_lane
        sample.reads = total_reads_for_sample
        self.session.commit()

    def update_sample_sequenced_at(self, internal_id: str, date: datetime):
        sample: Sample = self.get_sample_by_internal_id(internal_id)
        sample.last_sequenced_at = date
        self.session.commit()
