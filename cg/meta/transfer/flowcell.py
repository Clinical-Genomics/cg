# -*- coding: utf-8 -*-
import logging

from cg.store import models, Store
from cg.apps.stats import StatsAPI

log = logging.getLogger(__name__)


def flowcell(db: Store, stats_api: StatsAPI, flowcell_name: str) -> models.Flowcell:
    """Populate the database with the information."""
    existing_record = db.flowcell(flowcell_name)
    if existing_record:
        return existing_record
    stats_data = stats_api.flowcell(flowcell_name)
    new_record = db.add_flowcell(
        name=flowcell_name,
        sequencer=stats_data['sequencer'],
        sequenced=stats_data['date'],
    )
    for sample_data in stats_data['samples']:
        log.info(f"adding reads to sample: {sample_data['name']} - {sample_data['reads']}")
        sample_obj = db.sample(sample_data['name'])
        sample_obj.reads = sample_data['reads']
        new_record.samples.append(sample_obj)
    return new_record
