"""Handler to update data objects"""

from sqlalchemy.orm import Session

from cg.store.base import BaseHandler
from cg.store.models import Flowcell, Order, Sample


class UpdateHandler(BaseHandler):
    """Contains methods to update database objects."""

    def __init__(self, session: Session):
        super().__init__(session=session)
        self.session = session

    def update_flow_cell_has_backup(self, flow_cell: Flowcell, has_backup: bool) -> None:
        flow_cell.has_backup = has_backup
        self.session.commit()

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
