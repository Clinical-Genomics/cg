# -*- coding: utf-8 -*-
import logging

import click
from sqlalchemy.exc import IntegrityError
from chanjo.store import api
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



    # local case_id=${1?'missing input - case id'};
    # local sample_id;
    # for sample_id in $(cglims get ${case_id} sample_id);
    # do
    #     ( echo "working on sample: ${sample_id}" 1>&2 );
    #     local coverage_bed;
    #     if coverage_bed=$(housekeeper get --sample "${sample_id}" --category coverage); then
    #         local case_id=$(cglims get ${sample_id} case_id);
    #         local family_id=$(cglims get ${sample_id} familyID);
    #         local sample_name=$(cglims get ${sample_id} name);
    #         chanjo load --group "${case_id}" --group-name "${family_id}" --name "${sample_name}" "${coverage_bed}";
    #     else
    #         ( echo "missing coverage output for: ${sample_id}" 1>&2 );
    #     fi;
    # done;
    # return 0
