# -*- coding: utf-8 -*-
import logging

import click
from path import Path
import ruamel.yaml

from . import apps
from .utils import parse_caseid

log = logging.getLogger(__name__)


def check_root(context, case_info):
    root_dir = Path(context.obj['analysis_root'])
    family_dir = root_dir.joinpath(case_info['customer_id'], case_info['family_id'])
    if not family_dir.exists():
        log.error("family directory not found: %s", family_dir)
        context.abort()


@click.command('mip-config')
@click.argument('case_id')
@click.pass_context
def mip_config(context, case_id):
    """Generate a MIP config from LIMS data."""
    case_info = parse_caseid(case_id)
    family_dir = check_root(context, case_info)
    config_file = "{}_pedigree.yaml".format(case_info['family_id'])
    config_path = family_dir.joinpath(config_file)

    log.debug("get config data: %s", case_info['case_id'])
    lims_api = apps.lims.connect(context.obj)
    data = apps.lims.config(lims_api, case_info['customer_id'], case_info['family_id'])

    if case_info['extra']:
        log.info("update config with suffic: %s", case_info['extra'])
        apps.lims.extend_case(data, case_info['extra'])

    with config_path.open('w') as out_handle:
        click.echo(ruamel.yaml.round_trip_dump(data), file=out_handle)
    log.info("wrote config to: %s", config_path)


@click.command()
@click.option('--source', '-s', type=click.Choice(['prod', 'archive']), default='prod')
@click.pass_context
def reruns(context, source='prod'):
    """Return reruns marked in Scout (old)."""
    scout_db = apps.scoutprod.connect(context.obj)
    if source == 'prod':
        for scout_case in apps.scoutprod.get_reruns(scout_db):
            click.echo(scout_case['_id'])

    elif source == 'archive':
        scoutold_db = apps.scoutold.connect(context.obj)
        for scout_case in apps.scoutold.get_reruns(scoutold_db):
            case_id = scout_case['_id'].replace('_', '-', 1)
            # lookup requested case in current Scout
            if apps.scoutprod.get_case(scout_db, case_id):
                pass
            else:
                click.echo(case_id)


@click.command('mip-panel')
@click.argument('case_id')
@click.pass_context
def mip_panel(context, case_id):
    """Generate an aggregated panel for MIP."""
    case_info = parse_caseid(case_id)
    lims_api = apps.lims.connect(context.obj)
    samples = lims_api.case(case_info['customer_id'], case_info['family_id'])

    # fetch default panels
    default_panels = set()
    for lims_sample in samples:
        default_panels.update(apps.lims.sample_panels(lims_sample))

    # convert default panels to all panels
    all_panels = apps.lims.convert_panels(case_info['customer_id'], default_panels)
    log.debug("determined panels to use: %s", ', '.join(all_panels))

    family_dir = check_root(context, case_info)
    panel_path = family_dir.joinpath('aggregated_master.bed')

    adapter = apps.scoutprod.connect_adapter(context.obj)
    apps.scoutprod.export_panels(adapter, all_panels)
    log.info("wrote aggregated gene panel: %s", panel_path)
