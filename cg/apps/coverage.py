# -*- coding: utf-8 -*-
import logging

import click
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from chanjo.store import api, models
from chanjo.load.sambamba import load_transcripts

from .omim import OMIM_GENE_IDS

log = logging.getLogger(__name__)


class Coverage(api.ChanjoDB):

    def __init__(self, config):
        """Connect to the chanjo coverage database."""
        super(Coverage, self).__init__(uri=config['chanjo']['database'])

    def validate(self, case_id):
        """Validate samples uploaded in the database."""
        query = self.query(
            models.Sample,
            func.avg(models.TranscriptStat.mean_coverage).label('mean_coverage'),
            func.avg(models.TranscriptStat.completeness_10).label('completeness_10'),
        ).join(
            models.TranscriptStat.sample,
            models.TranscriptStat.transcript
        ).filter(
            models.Sample.group_id == case_id,
            models.Transcript.gene_id.in_(OMIM_GENE_IDS)
        ).group_by(models.TranscriptStat.sample_id)
        return query


def connect(config):
    """Connect to the chanjo coverage database."""
    chanjo_db = api.ChanjoDB(uri=config['chanjo']['database'])
    return chanjo_db


def add(chanjo_db, case_id, family_name, sample_id, sample_name, bed_stream, source=None):
    """Add coverage for an analysis to the database."""
    result = load_transcripts(bed_stream, sample_id=sample_id, group_id=case_id, source=source)
    result.sample.name = sample_name
    result.sample.group_name = family_name
    try:
        chanjo_db.add(result.sample)
        with click.progressbar(result.models, length=result.count,
                               label='loading transcripts') as bar:
            for tx_model in bar:
                chanjo_db.add(tx_model)
        chanjo_db.save()
    except IntegrityError as error:
        log.debug(error.message)
        chanjo_db.session.rollback()
        raise error


def sample(sample_id):
    """Get sample from database."""
    return models.Sample.query.get(sample_id)


def delete(chanjo_db, sample_obj):
    """Delete sample from database."""
    chanjo_db.session.delete(sample_obj)
    chanjo_db.save()
