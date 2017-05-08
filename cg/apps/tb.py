# -*- coding: utf-8 -*-
import datetime
import logging

from trailblazer.store import api
from trailblazer.add.commit import commit_analysis
from trailblazer.analyze.cli import environ_email
from trailblazer.analyze.start import start_mip, build_pending
from path import Path
import ruamel.yaml

log = logging.getLogger(__name__)


def connect(config):
    """Connect to the Trailblazer database."""
    tb_db = api.connect(config['trailblazer']['database'])
    return tb_db


def start_analysis(config, case_info, hg38=False, execute=True, force=False,
                   skip_validation=False, prioritize=False, email=None):
    """Start analysis run."""
    tb_db = connect(config)
    customer_id = case_info['customer_id']
    family_id = case_info['raw']['family_id']
    case_id = case_info['raw']['case_id']
    cc_path = Path(config['trailblazer']['analysis_root']).joinpath(customer_id)
    if not force:
        check_setup(tb_db, case_id)

    pedigree_path = cc_path.joinpath("{0}/{0}_pedigree.yaml".format(family_id))
    if not pedigree_path.exists():
        raise ValueError("pedigree YAML doesn't exist: {}".format(pedigree_path))
    with pedigree_path.open() as in_handle:
        ped_data = ruamel.yaml.round_trip_load(in_handle)
        analysis_type = case_analysis_type(ped_data)
        # set max guassian flag for SNVs if WGS analysis
        max_gaussian = True if analysis_type == 'wgs' else False

    global_config = (config['trailblazer']['mip_config_hg38'] if hg38 else
                     config['trailblazer']['mip_config'])
    executable = config['trailblazer']['mip_exe']
    email = email or environ_email()

    flags = [('--qccollect_skip_evaluation', '1')] if skip_validation else None
    priority = 'high' if prioritize else 'normal'
    process = start_mip(config=global_config, family_id=family_id, ccp=cc_path,
                        executable=executable, email=email, max_gaussian=max_gaussian,
                        execute=execute, flags=flags, priority=priority)

    if execute:
        process.wait()
        if process.returncode != 0:
            raise ValueError("check output, error starting analysis: {}"
                             .format(case_id))

        # add pending entry to database
        new_entry = build_pending(case_id, cc_path)
        if email:
            user = api.user(email)
            new_entry.user = user

        commit_analysis(tb_db, new_entry)
        tb_db.commit()


def check_setup(tb_db, case_id):
    """Perform pre-analysis checks."""
    if api.is_running(case_id):
        raise ValueError("case already running: {}".format(case_id))


def case_analysis_type(ped_data):
    """Get overall analysis type for a case."""
    analysis_types = set(sample['analysis_type'] for sample in ped_data['samples'])
    if len(analysis_types) == 1:
        return analysis_types.pop()
    elif 'wgs' in analysis_types:
        return 'wgs'
    else:
        raise ValueError("unknown analysis type: {}".format(analysis_types))


def recently_completed(tb_db):
    """Return recently completed analyses."""
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=3)
    analysis_q = api.analyses(since=week_ago, is_ready=True)
    return analysis_q


def analyses_running(tb_db):
    running_q = api.analyses(status=['pending', 'running'])
    return running_q.count()


def latest_status(tb_db, case_name, status):
    """Check if the latest run of a case has failed."""
    latest_case_run = api.analyses(analysis_id=case_name).first()
    if latest_case_run is None:
        return False
    elif latest_case_run.status == status:
        return True
    else:
        return False
