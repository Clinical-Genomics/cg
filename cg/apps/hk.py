# -*- coding: utf-8 -*-
import logging
import pkg_resources

from housekeeper.store import api
from housekeeper.store.utils import get_rundir
from housekeeper.pipelines.mip4.scout import prepare_scout
from housekeeper.pipelines.cli import LOADERS, link_records
from housekeeper.pipelines.general import commit_analysis
import ruamel.yaml

from cg.exc import MissingFileError

log = logging.getLogger(__name__)


def connect(config):
    """Connect to the Housekeeper database."""
    hk_db = api.manager(config['housekeeper']['database'])
    return hk_db


def latest_run(hk_db, case_id):
    """Get the latest analysis for a case."""
    case_obj = api.case(case_id)
    if case_obj is None or len(case_obj.runs) == 0:
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


def observations(hk_db, analysis_obj):
    """Parse analysis record for uploading to LoqusDB."""
    existing_ped = api.assets(run_id=analysis_obj.id, category='pedigree').first()
    existing_vcf = api.assets(run_id=analysis_obj.id, category='vcf-research-bin').first()
    return dict(ped=existing_ped.path, vcf=existing_vcf.path)


def rundir(config, analysis_obj):
    """Get root directory for a run."""
    root_path = get_rundir(config['housekeeper']['root'], analysis_obj.case.name, analysis_obj)
    return root_path


def add_asset(hk_db, analysis_obj, asset_path, category, archive_type=None, sample=None):
    """Add a new asset to an existing analysis run."""
    # check existing asset
    existing_asset = api.assets(run_id=analysis_obj.id, category=category).first()
    if existing_asset:
        log.warn("existing asset exists!")
        return existing_asset

    new_asset = api.add_asset(analysis_obj, asset_path, category, archive_type, sample=sample)
    new_asset.path = asset_path
    analysis_obj.assets.append(new_asset)
    log.info("add asset: %s", new_asset.path)
    hk_db.commit()
    return new_asset


def to_analyze(hk_db):
    """Fetch cases to be analyzed."""
    cases_q = api.cases(missing='analyzed', onhold=False)
    return cases_q


def add(hk_db, root_path, analysis_config, pipeline='mip4', force=False):
    """Add analyses from different pipelines."""
    default_ref = "pipelines/references/{}.yaml".format(pipeline)
    references = pkg_resources.resource_string('housekeeper', default_ref)
    reference_data = ruamel.yaml.safe_load(references)
    loader = LOADERS[pipeline]
    data = loader(analysis_config, reference_data, force=force)
    records = link_records(data)
    case_name = records['case'].name
    commit_analysis(hk_db, root_path, records['case'], records['run'])
    log.info("added new analysis: %s", case_name)
    sample_ids = ', '.join(sample.lims_id for sample in records['run'].samples)
    log.info("including samples: %s", sample_ids)
