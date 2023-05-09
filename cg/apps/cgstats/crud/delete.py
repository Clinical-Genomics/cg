import logging

from typing import List, Optional

from alchy import Session
from cg.apps.cgstats.crud.find import FindHandler

from cg.apps.cgstats.db.models import Flowcell

log = logging.getLogger(__name__)


def delete_flowcell(session: Session, flowcell_name: str):
    flow_cell: Optional[Flowcell] = FindHandler().get_flow_cell_by_name(
        flow_cell_name=flowcell_name
    )

    if flow_cell:
        log.info("Removing entry %s in from cgstats", flow_cell.flowcellname)
        session.delete(flow_cell)
        session.commit()
