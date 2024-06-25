"""Handler to update data objects"""

from sqlalchemy.orm import Session

from cg.constants import FlowCellStatus
from cg.store.base import BaseHandler
from cg.store.models import Flowcell, Order, Sample, IlluminaSequencingRun


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

    def update_illumina_sequencing_run_availability(
        self, sequencing_run: IlluminaSequencingRun, data_availability: FlowCellStatus
    ) -> IlluminaSequencingRun:
        """Update the status of an Illumina sequencing run."""
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
