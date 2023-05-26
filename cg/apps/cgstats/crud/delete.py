import logging

from typing import Optional

from cg.apps.cgstats.db.models import Flowcell
from cg.apps.cgstats.stats import StatsAPI

log = logging.getLogger(__name__)


def delete_flowcell(manager: StatsAPI, flowcell_name: str):
    flow_cell: Optional[Flowcell] = manager.find_handler.get_flow_cell_by_name(
        flow_cell_name=flowcell_name
    )

    if flow_cell:
        log.info("Removing entry %s in from cgstats", flow_cell.flowcellname)
        manager.delete(flow_cell)
        manager.commit()
