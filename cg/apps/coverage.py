# -*- coding: utf-8 -*-
import logging

import click
from sqlalchemy.exc import IntegrityError
from chanjo.store import api
from chanjo.store.models import Sample
from chanjo.load.sambamba import load_transcripts

log = logging.getLogger(__name__)


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
    return Sample.query.get(sample_id)


def delete(chanjo_db, sample_obj):
    """Delete sample from database."""
    chanjo_db.session.delete(sample_obj)
    chanjo_db.save()
