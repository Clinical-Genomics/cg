# -*- coding: utf-8 -*-
from datetime import datetime
import logging

import click
from path import Path
import ruamel.yaml

from . import apps
from .utils import parse_caseid

log = logging.getLogger(__name__)


def check_root(context, case_info):
    root_dir = Path(context.obj['analysis_root'])
    family_dir = root_dir.joinpath(case_info['customer_id'], case_info['raw']['family_id'])
    if not family_dir.exists():
        log.error("family directory not found: %s", family_dir)
        context.abort()
    return family_dir


@click.command('mip-config')
@click.option('-p', '--print', 'print_output', is_flag=True, help='print to console')
@click.argument('case_id')
@click.pass_context
def mip_config(context, print_output, case_id):
    """Generate a MIP config from LIMS data."""
    case_info = parse_caseid(case_id)

    log.debug("get config data: %s", case_info['case_id'])
    lims_api = apps.lims.connect(context.obj)
    data = apps.lims.config(lims_api, case_info['customer_id'], case_info['family_id'])

    if case_info['extra']:
        log.info("update config with suffix: %s", case_info['extra'])
        apps.lims.extend_case(data, case_info['extra'])

    raw_output = ruamel.yaml.round_trip_dump(data, indent=4, block_seq_indent=2)
    if print_output:
        click.echo(raw_output.decode())
    else:
        family_dir = check_root(context, case_info)
        config_file = "{}_pedigree.yaml".format(case_info['raw']['family_id'])
        config_path = family_dir.joinpath(config_file)
        with config_path.open('w') as out_handle:
            click.echo(raw_output.decode(), file=out_handle)
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
@click.option('-p', '--print', 'print_output', is_flag=True, help='print to console')
@click.argument('case_id')
@click.pass_context
def mip_panel(context, print_output, case_id):
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

    adapter = apps.scoutprod.connect_adapter(context.obj)
    bed_lines = apps.scoutprod.export_panels(adapter, all_panels)

    if print_output:
        for bed_line in bed_lines:
            click.echo(bed_line)
    else:
        family_dir = check_root(context, case_info)
        panel_path = family_dir.joinpath('aggregated_master.bed')
        with panel_path.open('w') as out_handle:
            click.echo('\n'.join(bed_lines), file=out_handle)
        log.info("wrote aggregated gene panel: %s", panel_path)


@click.command()
@click.option('-a', '--answered-out', is_flag=True, help='fill in answered out status')
@click.argument('case_id')
@click.pass_context
def update(context, answered_out, case_id):
    """Fill in information in Housekeeper."""
    if answered_out:
        hk_db = apps.hk.connect(context.obj)
        lims_api = apps.lims.connect(context.obj)
        log.debug("get case from housekeeper")
        hk_case = apps.hk.api.case(case_id)
        log.debug("loop over related samples from most recent run")
        delivery_dates = []
        hk_run = hk_case.current
        for hk_sample in hk_run.samples:
            log.debug("lookup if sample has been delivered in LIMS")
            delivery_date = lims_api.is_delivered(hk_sample.lims_id)
            if delivery_date is None:
                log.warn("sample not delivered: %s", hk_sample.lims_id)
                context.abort()
            delivery_dates.append(delivery_date)
        latest_date = sorted(delivery_dates)[-1]
        log.debug("fillin answered out date in HK")
        hk_run.answeredout_at = datetime.combine(latest_date, datetime.min.time())
        hk_db.commit()
        log.info("run 'answered out' date updated: %s", case_id)


@click.command()
@click.argument('process_id')
@click.pass_context
def check(context, process_id):
    """Check samples in LIMS and optionally update them."""
    admin_db = apps.admin.connect(context.obj)
    lims_api = apps.lims.connect(context.obj)
    samples = list(apps.lims.process_to_samples(lims_api, process_id))
    uniq_tags = set(sample['sample'].udf['Sequencing Analysis'] for sample in samples)
    apptag_map = apps.admin.map_apptags(admin_db, uniq_tags)
    apps.lims.check_samples(lims_api, samples, apptag_map)


@click.command()
@click.option('-s', '--setup/--no-setup', default=True,
              help='perform setup before starting analysis')
@click.option('--execute/--no-execute', default=True, help='skip running MIP')
@click.option('-f', '--force', is_flag=True, help='skip pre-analysis checks')
@click.option('--hg38', is_flag=True, help='run with hg38 settings')
@click.argument('case_id')
@click.pass_context
def start(context, setup, execute, force, hg38, case_id):
    """Start a MIP analysis."""
    case_info = parse_caseid(case_id)
    if setup:
        log.info('generate aggregated gene panel')
        context.invoke(mip_panel, case_id=case_id)
        log.info('generate analysis pedigree')
        context.invoke(mip_config, case_id=case_id)

    log.info("start analysis for: %s", case_id)
    apps.tb.start_analysis(context.obj, case_info, hg38=hg38, force=force,
                           execute=execute)


@click.command()
@click.option('-f', '--force', is_flag=True, help='skip pre-upload checks')
@click.argument('case_id')
@click.pass_context
def coverage(context, force, case_id):
    """Upload coverage for an analysis (latest)."""
    chanjo_db = apps.coverage.connect(context.obj)
    hk_db = apps.hk.connect(context.obj)
    lims_api = apps.lims.connect(context.obj)
    case_info = parse_caseid(case_id)
    # get latest analysis for the case
    latest_run = apps.hk.latest_run(case_info['raw']['case_id'])
    if latest_run is None:
        click.echo("No run found for the case!")
        context.abort()

    if not force and latest_run.extra.coverage_date:
        click.echo("Coverage already uploaded for run: %s", latest_run.extra.coverage_date.date())
    else:
        for sample_data in apps.hk.coverage(hk_db, latest_run):
            chanjo_sample = apps.coverage.sample(sample_data['sample_id'])
            if chanjo_sample:
                log.warn("removing existing sample: %s", chanjo_sample.id)
                apps.coverage.delete(chanjo_db, chanjo_sample)

            lims_sample = lims_api.sample(sample_data['sample_id'])
            log.info("adding coverage for sample: %s", sample_data['sample_id'])
            with open(sample_data['bed_path']) as bed_stream:
                apps.coverage.add(
                    chanjo_db,
                    case_id=case_info['raw']['case_id'],
                    family_name=case_info['raw']['family_id'],
                    sample_id=sample_data['sample_id'],
                    sample_name=lims_sample.name,
                    bed_stream=bed_stream,
                    source=sample_data['bed_path']
                )
        latest_run.extra.coverage_date = datetime.now()
        hk_db.commit()
