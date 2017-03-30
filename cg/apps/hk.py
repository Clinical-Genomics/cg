# -*- coding: utf-8 -*-
import logging

from housekeeper.store import api

log = logging.getLogger(__name__)


def connect(config):
    """Connect to the Housekeeper database."""
    hk_db = api.manager(config['housekeeper']['database'])
    return hk_db


def latest_run(case_id):
    """Get the latest analysis for a case."""
    case_obj = api.case(case_id)
    if case_obj is None:
        return None
    return case_obj.runs[0]


def coverage(hk_db, analysis_obj):
    """Parse analysis record for uploading coverage."""
    for sample_obj in analysis_obj.samples:
        coverage_bed = api.assets(sample=sample_obj.lims_id, category='coverage',
                                  run_id=analysis_obj.id).first()
        if coverage_bed is None:
            log.warn("no coverage output found for sample: %s", sample_obj.lims_id)
            continue

        yield dict(sample_id=sample_obj.lims_id, bed_path=coverage_bed.path)
