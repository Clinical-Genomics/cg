# -*- coding: utf-8 -*-
import logging

from clinstatsdb.db import api
from clinstatsdb.analysis.cli import test_analysis
from clinstatsdb.analysis.export import export_run
from clinstatsdb.analysis.mip import process_all
from clinstatsdb.analysis.models import Analysis
import ruamel.yaml

log = logging.getLogger(__name__)


def connect(config):
    """Connect to the database."""
    cgstats_db = api.connect(config['cgstats']['database'])
    return cgstats_db


def add(cgstats_db, case_id, qc_stream, sampleinfo_stream, force=False):
    """Add QC output from an analysis run."""
    sampleinfo = ruamel.yaml.safe_load(sampleinfo_stream)

    if not force and not test_analysis(sampleinfo):
        log.warn("analysis can't be loaded, use '--force'")
    else:
        old_analysis = Analysis.query.filter_by(analysis_id=case_id).first()
        if old_analysis:
            log.warn("removing old analysis")
            old_analysis.delete()
            cgstats_db.commit()

        metrics = ruamel.yaml.safe_load(qc_stream)
        log.debug("parsing analysis output")
        new_analysis = process_all(case_id, sampleinfo, metrics)
        log.info("adding analysis: %s", new_analysis.analysis_id)
        cgstats_db.add_commit(new_analysis)


def sequencing_status(cgstats_db, samples_data):
    """Update sample data from cgstats."""
    for sample_id, sample_data in samples_data.items():
        query = api.get_sample(sample_id)
        sample_obj = query.one()

        # fetch number of reads
        reads = sum(unaligned.readcounts for unaligned in sample_obj.unaligned)
        if reads < sample_data['expected_reads']:
            sample_data['sequenced_at'] = None
        else:
            sorted_dates = sorted(unaligned.demux.datasource.rundate for unaligned
                                  in sample_obj.unaligned)
            sample_data['sequenced_at'] = sorted_dates[-1]
