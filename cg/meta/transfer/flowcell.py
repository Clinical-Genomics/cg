# -*- coding: utf-8 -*-
import logging

from cg.store import models, Store
from cg.apps.stats import StatsAPI

log = logging.getLogger(__name__)


def flowcell(db: Store, stats_api: StatsAPI, flowcell_name: str) -> models.Flowcell:
    """Populate the database with the information."""
    stats_data = stats_api.flowcell(flowcell_name)
    record = db.flowcell(flowcell_name)
    if record is None:
        record = db.add_flowcell(
            name=flowcell_name,
            sequencer=stats_data['sequencer'],
            sequenced=stats_data['date'],
        )
    for sample_data in stats_data['samples']:
        log.debug(f"adding reads to sample: {sample_data['name']}")
        sample_obj = db.sample(sample_data['name'])
        if sample_obj is None:
            log.warning(f"unable to find sample: {sample_data['name']}")
            continue
        sample_obj.reads = sample_data['reads']
        enough_reads = sample_obj.reads > sample_obj.application_version.application.expected_reads
        newest_date = ((sample_obj.sequenced_at is None) or
                       (record.sequenced_at > sample_obj.sequenced_at))
        if enough_reads and newest_date:
            sample_obj.sequenced_at = record.sequenced_at
        record.samples.append(sample_obj)
        log.info(f"added reads to sample: {sample_data['name']} - {sample_data['reads']} "
                 f"[{'DONE' if enough_reads else 'NOT DONE'}]")
    return record
