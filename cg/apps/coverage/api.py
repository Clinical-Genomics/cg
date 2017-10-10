# -*- coding: utf-8 -*-
from typing import List
import logging
import io
from pathlib import Path

from chanjo.store.api import ChanjoDB
from chanjo.store import models
from chanjo.load.sambamba import load_transcripts
import click
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from .omim import OMIM_GENE_IDS

LOG = logging.getLogger(__name__)


class ChanjoAPI(ChanjoDB):

    """Interface to Chanjo, the coverage analysis tool."""

    def __init__(self, config: dict):
        super(ChanjoAPI, self).__init__(uri=config['chanjo']['database'])

    def upload(self, sample_id: str, sample_name: str, group_id: str, group_name: str,
               bed_stream: io.TextIOWrapper):
        """Upload coverage for a sample."""
        source = str(Path(bed_stream.name).absolute())
        result = load_transcripts(bed_stream, sample_id=sample_id, group_id=group_id,
                                  source=source, threshold=10)
        result.sample.name = sample_name
        result.sample.group_name = group_name

        try:
            self.add(result.sample)
            with click.progressbar(result.models, length=result.count,
                                   label=f"loading {sample_id}") as progress_bar:
                for tx_model in progress_bar:
                    self.add(tx_model)
            self.save()
        except IntegrityError as error:
            self.session.rollback()
            raise error
    
    def sample(self, sample_id: str) -> models.Sample:
        """Fetch sample from the database."""
        return models.Sample.get(sample_id)

    def delete_sample(self, sample_obj: models.Sample):
        """Delete sample from database."""
        self.delete_commit(sample_obj)

    def omim_coverage(self, samples: List[models.Sample]) -> dict:
        """Calculate coverage for OMIM panel."""
        sample_ids = [sample.id for sample in samples]
        query = self.query(
            models.TranscriptStat.sample_id.label('sample_id'),
            func.avg(models.TranscriptStat.mean_coverage).label('mean_coverage'),
            func.avg(models.TranscriptStat.completeness_10).label('mean_completeness'),
        ).join(
            models.TranscriptStat.transcript,
        ).filter(
            models.TranscriptStat.sample_id.in_(sample_ids),
            models.Transcript.gene_id.in_(OMIM_GENE_IDS),
        ).group_by(models.TranscriptStat.sample_id)
        data = {result.sample_id: {
            'mean_coverage': result.mean_coverage,
            'mean_completeness': result.mean_completeness,
        } for result in query}
        return data
