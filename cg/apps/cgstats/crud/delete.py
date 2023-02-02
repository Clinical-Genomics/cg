import logging

from typing import List, Optional

from cg.apps.cgstats.crud.find import get_flowcell_id
from cg.apps.cgstats.db import models
from cg.apps.cgstats.stats import StatsAPI

log = logging.getLogger(__name__)


def delete_flowcell(manager: StatsAPI, flowcell_name: str):
    flowcell_id: Optional[int] = get_flowcell_id(flowcell_name=flowcell_name)

    if flowcell_id:
        flowcell: List[models.Flowcell] = manager.Flowcell.query.filter_by(
            flowcell_id=flowcell_id
        ).all()
        for entry in flowcell:
            log.info("Removing entry %s in from cgstats", entry.flowcellname)
            manager.delete(flowcell)
            manager.commit()
