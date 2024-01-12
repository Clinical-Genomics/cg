"""Handler to update data objects"""

from sqlalchemy.orm import Session

from cg.store.api.base import BaseHandler
from cg.store.models import Flowcell


class UpdateHandler(BaseHandler):
    """Contains methods to update database objects."""

    def __init__(self, session: Session):
        super().__init__(session=session)
        self.session = session

    def update_flow_cell_has_backup(self, flow_cell: Flowcell, has_backup: bool) -> None:
        flow_cell.has_backup = has_backup
        self.session.commit()
