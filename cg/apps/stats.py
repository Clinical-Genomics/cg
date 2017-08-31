# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Iterator

import alchy
import sqlalchemy as sqa

from cgstats.db import api, models


class StatsAPI(alchy.Manager):

    Project = models.Project
    Sample = models.Sample
    Unaligned = models.Unaligned
    Supportparams = models.Supportparams
    Datasource = models.Datasource
    Demux = models.Demux
    Flowcell = models.Flowcell

    def __init__(self, config: dict):
        alchy_config = dict(SQLALCHEMY_DATABASE_URI=config['cgstats']['database'])
        super(StatsAPI, self).__init__(config=alchy_config, Model=models.Model)
        self.root_dir = Path(config['cgstats']['root'])

    def flowcell(self, flowcell_name: str) -> dict:
        """Fetch information about a flowcell."""
        record = self.Flowcell.query.filter_by(flowcellname=flowcell_name).first()
        data = {
            'name': record.flowcellname,
            'sequencer': record.demux[0].datasource.machine,
            'sequencer_type': record.hiseqtype,
            'date': record.time,
            'samples': []
        }
        for sample in self.sample_reads(record):
            raw_samplename = sample.name.split('_', 1)[0]
            curated_samplename = raw_samplename.rstrip('AB')
            data['samples'].append({
                'name': curated_samplename,
                'reads': sample.reads,
            })
        return data

    def sample_flowcells(self, sample_obj: models.Sample) -> Iterator[models.Flowcell]:
        """Fetch all flowcells for a sample."""
        return (
            self.Flowcell.query
            .join(models.Flowcell.demux, models.Demux.unaligned)
            .filter(models.Unaligned.sample == sample_obj)
        )

    def sample_reads(self, flowcell_obj: models.Flowcell) -> Iterator:
        """Calculate reads for a sample."""
        query = (
            self.session.query(
                models.Sample.samplename.label('name'),
                sqa.func.sum(models.Unaligned.readcounts).label('reads'),
            )
            .join(
                models.Sample.unaligned,
                models.Sample.demuxes
            )
            .filter(models.Demux.flowcell == flowcell_obj)
            .group_by(models.Sample.samplename)
        )
        return query

    def sample(self, sample_name: str) -> models.Sample:
        """Fetch a sample for the database by name."""
        return api.get_sample(sample_name).first()

    def fastqs(self, sample_obj: models.Sample) -> Iterator[Path]:
        """Fetch FASTQ files for a sample."""
        base_pattern = "*{}/Unaligned*/Project_*/Sample_{}/*.fastq.gz"
        for flowcell_obj in self.sample_flowcells(sample_obj):
            pattern = base_pattern.format(flowcell_obj.flowcellname, sample_obj.samplename)
            files = self.root_dir.glob(pattern)
            yield from files
