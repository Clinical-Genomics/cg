# -*- coding: utf-8 -*-
import logging

from housekeeper.store import api
from housekeeper.store.utils import get_rundir
from housekeeper.pipelines.mip4.scout import prepare_scout

from cg.exc import MissingFileError

log = logging.getLogger(__name__)


def connect(config):
    """Connect to the Housekeeper database."""
    hk_db = api.manager(config['housekeeper']['database'])
    return hk_db


def latest_run(hk_db, case_id):
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


def genotypes(hk_db, analysis_obj):
    """Parse analysis record for uploading genotypes."""
    # first try to find a "gBCF"
    bcf_obj = api.assets(run_id=analysis_obj.id, category='gbcf').first()
    if bcf_obj is None:
        log.warn("can't find gBCF, looking up raw BCF file")
        bcf_obj = api.assets(run_id=analysis_obj.id, category='bcf-raw').first()

    if bcf_obj is None:
        log.error("BCF file missing")
        raise MissingFileError("gBCF/BCF not found")

    qc_obj = api.assets(run_id=analysis_obj.id, category='qc').first()
    return dict(bcf_path=bcf_obj.path, qc_path=qc_obj.path)


def qc(hk_db, analysis_obj):
    """Parse analysis record for adding QC output."""
    qc_obj = api.assets(run_id=analysis_obj.id, category='qc').first()
    sampleinfo_obj = api.assets(run_id=analysis_obj.id, category='sampleinfo').first()
    return dict(qc_path=qc_obj.path, sampleinfo_path=sampleinfo_obj.path)


def visualize(hk_db, analysis_obj, madeline_exe, root_path):
    """Parse analysis record for uploading to Scout."""
    log.info("create/replace Scout load config")
    existing_conf = api.assets(run_id=analysis_obj.id, category='scout-config').first()
    if existing_conf:
        log.info("delete existing scout config: %s", existing_conf.path)
        api.delete_asset(existing_conf)
    existing_mad = api.assets(run_id=analysis_obj.id, category='madeline').first()
    if existing_mad:
        log.info("delete existing madeline: %s", existing_mad.path)
        api.delete_asset(existing_mad)
    hk_db.commit()

    prepare_scout(analysis_obj, root_path, madeline_exe)
    hk_db.commit()

    scout_config = api.assets(run_id=analysis_obj.id, category='scout-config').first()
    return scout_config.path


def rundir(config, analysis_obj):
    """Get root directory for a run."""
    root_path = get_rundir(config['housekeeper']['root'], analysis_obj.case.name, analysis_obj)
    return root_path


def add_asset(hk_db, analysis_obj, asset_path, category, archive_type=None, sample=None):
    """Add a new asset to an existing analysis run."""
    new_asset = api.add_asset(analysis_obj, asset_path, category, archive_type, sample=sample)
    new_asset.path = asset_path
    analysis_obj.assets.append(new_asset)
    log.info("add asset: %s", new_asset.path)
    hk_db.commit()
    return new_asset
