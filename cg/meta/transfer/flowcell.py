# -*- coding: utf-8 -*-
import logging
from typing import List

from cg.store import models, Store
from cg.apps.stats import StatsAPI
from cg.apps.hk import HousekeeperAPI

LOG = logging.getLogger(__name__)


class TransferFlowcell():

    def __init__(self, db: Store, stats_api: StatsAPI, hk_api: HousekeeperAPI=None):
        self.db = db
        self.stats = stats_api
        self.hk = hk_api

    def transfer(self, flowcell_name: str, store: bool=True) -> models.Flowcell:
        """Populate the database with the information."""
        stats_data = self.stats.flowcell(flowcell_name)
        record = self.db.flowcell(flowcell_name)
        if record is None:
            record = self.db.add_flowcell(
                name=flowcell_name,
                sequencer=stats_data['sequencer'],
                sequencer_type=stats_data['sequencer_type'],
                date=stats_data['date'],
            )
        for sample_data in stats_data['samples']:
            LOG.debug(f"adding reads to sample: {sample_data['name']}")
            sample_obj = self.db.sample(sample_data['name'])
            if sample_obj is None:
                LOG.warning(f"unable to find sample: {sample_data['name']}")
                continue
            
            if store:
                # store FASTQ files
                stats_sample = self.stats.sample(sample_data['name'])
                fastq_files = self.stats.fastqs(stats_sample)
                self.store_fastqs(sample_obj.internal_id, map(str, fastq_files))

            sample_obj.reads = sample_data['reads']
            enough_reads = (sample_obj.reads >
                            sample_obj.application_version.application.expected_reads)
            newest_date = ((sample_obj.sequenced_at is None) or
                           (record.sequenced_at > sample_obj.sequenced_at))
            if enough_reads and newest_date:
                sample_obj.sequenced_at = record.sequenced_at
            record.samples.append(sample_obj)
            LOG.info(f"added reads to sample: {sample_data['name']} - {sample_data['reads']} "
                     f"[{'DONE' if enough_reads else 'NOT DONE'}]")

        return record

    def store_fastqs(self, sample_id: str, fastq_files: List[str]):
        """Store FASTQ files for a sample in housekeeper."""
        hk_bundle = self.hk.bundle(sample_id)
        if hk_bundle is None:
            hk_bundle = self.hk.new_bundle(sample_id)
            self.hk.add_commit(hk_bundle)
            new_version = self.hk.new_version(created_at=hk_bundle.created_at)
            hk_bundle.versions.append(new_version)
            self.hk.commit()
            LOG.info(f"added new Housekeeper bundle: {hk_bundle.name}")

        with self.hk.session.no_autoflush:
            hk_version = hk_bundle.versions[0]
            for fastq_file in fastq_files:
                if self.hk.files(path=fastq_file).first() is None:
                    LOG.info(f"found FASTQ file: {fastq_file}")
                    new_file = self.hk.new_file(path=fastq_file, tags=[self.hk.tag('fastq')])
                    hk_version.files.append(new_file)
            self.hk.commit()
