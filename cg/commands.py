# -*- coding: utf-8 -*-
from collections import Counter, namedtuple
import os.path
from datetime import datetime
import logging

import click
from loqusdb.exceptions import CaseError, VcfError
from housekeeper import exc as hk_exc
from path import Path
import ruamel.yaml

from . import apps
from .utils import parse_caseid, check_latest_run

log = logging.getLogger(__name__)
FakeAnalysis = namedtuple('FakeAnalysis', ['case_id', 'config_path'])


def check_root(context, case_info):
    """Compose and check if root analysis directory for a case exists.

    Aborts the Click CLI context if the family directory doesn't exist.

    Args:
        context (Object): Click context object
        case_info (dict): Parsed case id information

    Returns:
        path: root analysis directory for the family/case
    """
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
            if scout_db.case(case_id=scout_case['_id']):
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
    samples = lims_api.case(case_info['customer_id'], case_info['raw']['family_id'])

    # fetch default panels
    default_panels = set()
    for lims_sample in samples:
        default_panels.update(apps.lims.sample_panels(lims_sample))

    # convert default panels to all panels
    all_panels = apps.lims.convert_panels(case_info['customer_id'], default_panels)
    log.debug("determined panels to use: %s", ', '.join(all_panels))

    adapter = apps.scoutprod.connect(context.obj)
    bed_lines = apps.scoutprod.export_panels(adapter, all_panels)

    if print_output:
        for bed_line in bed_lines:
            click.echo(bed_line)
    else:
        family_dir = check_root(context, case_info)
        panel_path = family_dir.joinpath('aggregated_master.bed')
        with panel_path.open('w') as out_handle:
            click.echo('\n'.join(bed_lines).decode(), file=out_handle)
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
    admin_db = apps.admin.Application(context.obj)
    lims_api = apps.lims.connect(context.obj)
    samples = list(apps.lims.process_to_samples(lims_api, process_id))
    uniq_tags = set(sample['sample'].udf['Sequencing Analysis'] for sample in samples)
    apptag_map = admin_db.map_apptags(uniq_tags)
    apps.lims.check_samples(lims_api, samples, apptag_map)


@click.command()
@click.option('-s', '--setup/--no-setup', default=True,
              help='perform setup before starting analysis')
@click.option('--execute/--no-execute', default=True, help='skip running MIP')
@click.option('-f', '--force', is_flag=True, help='skip pre-analysis checks')
@click.option('--hg38', is_flag=True, help='run with hg38 settings')
@click.option('-e', '--email', help='email to send errors to')
@click.argument('case_id')
@click.pass_context
def start(context, setup, execute, force, hg38, email, case_id):
    """Start a MIP analysis."""
    case_info = parse_caseid(case_id)
    if setup:
        log.info('generate aggregated gene panel')
        context.invoke(mip_panel, case_id=case_id)
        log.info('generate analysis pedigree')
        context.invoke(mip_config, case_id=case_id)

    lims_api = apps.lims.connect(context.obj)
    lims_data = apps.lims.start(lims_api, case_info['customer_id'], case_info['raw']['family_id'])

    log.info("start analysis for: %s", case_id)
    apps.tb.start_analysis(context.obj, case_info, hg38=hg38, force=force, execute=execute,
                           skip_validation=lims_data['is_external'],
                           prioritize=lims_data['is_prio'], email=email)


@click.command('auto-start')
@click.option('--dry-run', is_flag=True, help='skip launching new runs')
@click.option('-e', '--email', help='email to send errors to')
@click.option('-f', '--force', is_flag=True, help='start all available runs')
@click.option('-r', '--running', default=20, help='how many runs to start at one time')
@click.pass_context
def auto_start(context, dry_run, email, force, running):
    """Automatically start analysis for sequenced cases."""
    hk_db = apps.hk.connect(context.obj)
    tb_db = apps.tb.connect(context.obj)
    cases = apps.hk.to_analyze(hk_db)

    log.info("%s cases can be started", cases.count())
    for case_obj in cases:
        analyses_running = apps.tb.analyses_running(tb_db)
        if not force and analyses_running >= running:
            log.warn("already %s analyses running, pausing", analyses_running)
            break

        log.debug("working on case: %s", case_obj.name)
        if not all(sample_obj.sequenced_at for sample_obj in case_obj.samples):
            log.warn("all samples not sequenced: %s", case_obj.name)
        elif len(case_obj.runs) != 0:
            log.warn("case already analyzed: %s", case_obj.name)
        elif apps.tb.api.is_running(case_obj.name):
            log.debug("already running, skipping: %s", case_obj.name)
        elif apps.tb.latest_status(tb_db, case_obj.name, 'failed'):
            log.debug("latest run has failed, skipping: %s", case_obj.name)
        elif apps.tb.latest_status(tb_db, case_obj.name, 'completed'):
            log.debug("latest run completed, skipping: %s", case_obj.name)
        else:
            log.info("starting case: %s", case_obj.name)
            if not dry_run:
                try:
                    context.invoke(start, case_id=case_obj.name, email=email)
                except ValueError as error:
                    log.error(error.args[0])
                except KeyError as error:
                    log.error("error creating config, sample: {}".format(error.args[0]))


@click.command()
@click.argument('mip_config_path', type=click.Path(exists=True), required=False)
@click.pass_context
def keep(context, mip_config_path):
    """Add recently completed analyses to Housekeeper."""
    tb_db = apps.tb.connect(context.obj)
    hk_db = apps.hk.connect(context.obj)
    if mip_config_path:
        analyses = [FakeAnalysis(os.path.basename(mip_config_path), mip_config_path)]
    else:
        analyses = apps.tb.recently_completed(tb_db)
    for analysis_obj in analyses:
        log.debug("working on case: %s", analysis_obj.case_id)
        try:
            root_path = context.obj['housekeeper']['root']
            with open(analysis_obj.config_path, 'r') as in_handle:
                mip_config_data = ruamel.yaml.safe_load(in_handle)
            apps.hk.add(hk_db, root_path, mip_config_data)
            log.info("added case to housekeeper: %s", analysis_obj.case_id)
        except hk_exc.AnalysisConflictError as error:
            log.debug('analysis already added to housekeeper')
        except hk_exc.MalformattedPedigreeError as error:
            log.error("bad PED formatting: %s", error.message)
        except hk_exc.AnalysisNotFinishedError as error:
            log.error("analysis not finished: %s", error.message)


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
    latest_run = check_latest_run(hk_db, context, case_info)

    coverage_date = latest_run.extra.coverage_date
    if not force and coverage_date:
        click.echo("Coverage already added for run: {}".format(coverage_date.date()))
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

        log.info("marking coverage added for case: %s", case_info['raw']['case_id'])
        latest_run.extra.coverage_date = latest_run.analyzed_at
        hk_db.commit()


@click.command()
@click.option('-f', '--force', is_flag=True, help='skip pre-upload checks')
@click.argument('case_id')
@click.pass_context
def genotypes(context, force, case_id):
    """Add VCF genotypes for an analysis run (latest)."""
    genotype_db = apps.gt.connect(context.obj)
    hk_db = apps.hk.connect(context.obj)
    lims_api = apps.lims.connect(context.obj)
    case_info = parse_caseid(case_id)
    latest_run = check_latest_run(hk_db, context, case_info)

    if not force and latest_run.extra.genotype_date:
        click.echo("Genotypes already added for run: {}"
                   .format(latest_run.extra.genotype_date.date()))
    else:
        assets = apps.hk.genotypes(hk_db, latest_run)
        apps.gt.add(genotype_db, assets['bcf_path'], force=force)
        samples_sex = apps.lims.case_sexes(lims_api, case_info['customer_id'],
                                           case_info['family_id'])
        with open(assets['qc_path']) as qcmetrics_stream:
            apps.gt.add_sex(genotype_db, samples_sex, qcmetrics_stream)

        log.info("marking genotypes added for case: %s", case_info['raw']['case_id'])
        latest_run.extra.genotype_date = latest_run.analyzed_at
        hk_db.commit()


@click.command()
@click.option('-f', '--force', is_flag=True, help='skip pre-upload checks')
@click.argument('case_id')
@click.pass_context
def qc(context, force, case_id):
    """Add QC metrics for an anlyais run (latest)."""
    hk_db = apps.hk.connect(context.obj)
    cgstats_db = apps.qc.connect(context.obj)
    case_info = parse_caseid(case_id)
    latest_run = check_latest_run(hk_db, context, case_info)

    if not force and latest_run.extra.qc_date:
        click.echo("QC already added for run: {}".format(latest_run.extra.qc_date.date()))
    else:
        assets = apps.hk.qc(hk_db, latest_run)
        with open(assets['qc_path']) as qc_stream, open(assets['sampleinfo_path']) as si_stream:
            apps.qc.add(cgstats_db, case_info['raw']['case_id'], qc_stream, si_stream, force=force)

        log.info("marking qc added for case: %s", case_info['raw']['case_id'])
        latest_run.extra.qc_date = latest_run.analyzed_at
        hk_db.commit()


@click.command()
@click.option('-f', '--force', is_flag=True, help='skip pre-upload checks')
@click.option('-t', '--threshold', default=5, help='rank score threshold')
@click.argument('case_id')
@click.pass_context
def visualize(context, force, threshold, case_id):
    """Add data to Scout for an analysis run (latest)."""
    hk_db = apps.hk.connect(context.obj)
    scout_db = apps.scoutprod.connect(context.obj)
    case_info = parse_caseid(case_id)
    latest_run = check_latest_run(hk_db, context, case_info)

    if not latest_run.pipeline_version.startswith('v4'):
        log.error("unsupported pipeline version: %s", latest_run.pipeline_version)
        context.abort()

    if not force and latest_run.extra.visualizer_date:
        click.echo("Run already added to scout: {}"
                   .format(latest_run.extra.visualizer_date.date()))
    else:
        config_path = apps.hk.visualize(hk_db, latest_run,
                                        context.obj['housekeeper']['madeline_exe'],
                                        context.obj['housekeeper']['root'])
        with open(config_path) as config_stream:
            config_data = ruamel.yaml.safe_load(config_stream)

        config_data['rank_score_threshold'] = threshold
        apps.scoutprod.add(scout_db, config_data, force=force)

        log.info("marking visualize added for case: %s", case_info['raw']['case_id'])
        latest_run.extra.visualizer_date = latest_run.analyzed_at
        hk_db.commit()


@click.command('delivery-report')
@click.argument('case_id')
@click.pass_context
def delivery_report(context, case_id):
    """Generate delivery report for the latest analysis."""
    log.info('connecting to databases')
    hk_db = apps.hk.connect(context.obj)
    lims_api = apps.lims.connect(context.obj)
    cgstats_db = apps.qc.connect(context.obj)
    admin_db = apps.admin.Application(context.obj)
    scout_db = apps.scoutprod.connect(context.obj)
    case_info = parse_caseid(case_id)
    latest_run = check_latest_run(hk_db, context, case_info)

    log.info('fetching data from LIMS')
    case_data = apps.lims.export(lims_api, case_info['customer_id'], case_info['family_id'])
    log.info('fetching data from cgstats')
    case_data = apps.qc.export_run(cgstats_db, case_data)
    log.info('generating report in cgadmin')
    template_out = admin_db.export_report(case_data)

    run_root = apps.hk.rundir(context.obj, latest_run)
    report_file = os.path.join(run_root, 'delivery-report.html')
    log.info("saving report to: %s", report_file)
    with click.open_file(report_file, mode='w', encoding='utf-8') as out_handle:
        out_handle.write(template_out)

    log.info("adding report to housekeeper")
    apps.hk.add_asset(hk_db, latest_run, report_file, 'export', archive_type='result')
    apps.scoutprod.report(scout_db, case_info['customer_id'], case_info['family_id'], report_file)


@click.command()
@click.argument('case_id')
@click.pass_context
def observations(context, case_id):
    """Add observations for a case."""
    case_info = parse_caseid(case_id)
    hk_db = apps.hk.connect(context.obj)
    latest_run = check_latest_run(hk_db, context, case_info)
    paths = apps.hk.observations(hk_db, latest_run)
    loqus_db = apps.loqus.connect(context.obj)

    existing_case = loqus_db.case(dict(case_id=case_id))
    if existing_case:
        log.warn("found observations for existing case - skipping: %s", case_id)
    else:
        try:
            apps.loqus.add(loqus_db, paths['ped'], paths['vcf'], case_id=case_id)
        except (CaseError, VcfError) as error:
            log.error(error)
            context.abort()


@click.command()
@click.option('-f', '--force', is_flag=True, help='skip pre-upload checks')
@click.argument('case_id')
@click.pass_context
def add(context, force, case_id):
    """Uplaod analysis results (latest) to various databases."""
    hk_db = apps.hk.connect(context.obj)
    admin_db = apps.admin.Application(context.obj)
    tb_db = apps.tb.connect(context.obj)
    case_info = parse_caseid(case_id)
    latest_run = check_latest_run(hk_db, context, case_info)

    if not force and latest_run.delivered_at:
        log.warn("Run already delivered: %s", latest_run.delivered_at.date())
    else:
        log.info("Add coverage")
        context.invoke(coverage, force=force, case_id=case_id)
        log.info("Add genotypes and sex information")
        context.invoke(genotypes, force=force, case_id=case_id)
        log.info("Add QC metrics")
        context.invoke(qc, force=force, case_id=case_id)
        if admin_db.customer(case_info['customer_id']).scout_access:
            if not force:
                log.info("Validate quality criteria")
                context.invoke(validate, case_id=case_id)
            else:
                log.warn("Skipping quality validation!")

            log.info("Add case and variants to Scout")
            context.invoke(visualize, force=force, case_id=case_id)
            log.info("Add delivery report to Scout upload")
            context.invoke(delivery_report, case_id=case_id)

            log.info("Add observations to local database, loqusdb")
            context.invoke(observations, case_id=case_id)

            # log.info("Send email about successful delivery")
            # email = apps.email.EMail(context.obj)
            # lims_api = apps.lims.connect(context.obj)
            # lims_samples = lims_api.case(case_info['customer_id'], case_info['raw']['family_id'])
            # ticket_id = lims_samples[0].project.name
            # email.deliver(ticket_id, case_info['raw']['family_id'])

        log.info("marking analysis run as delivered: %s", case_info['raw']['case_id'])
        latest_run.delivered_at = datetime.now()
        hk_db.commit()

        log.info("commenting on run log in trailblazer")
        analysis_log = (apps.tb.api.Analysis.query
                            .filter_by(case_id=case_info['raw']['case_id'],
                                       started_at=latest_run.analyzed_at)
                            .first())
        if analysis_log:
            message = 'analysis delivered! /cg'
            if analysis_log.comment:
                analysis_log.comment = "{}\n\n{}".format(message, analysis_log.comment)
            else:
                analysis_log.comment = message
            tb_db.commit()


@click.command()
@click.argument('case_id')
@click.pass_context
def validate(context, case_id):
    """Validate samples in a case."""
    case_info = parse_caseid(case_id)
    lims_api = apps.lims.connect(context.obj)
    lims_data = apps.lims.validate(lims_api, case_info['customer_id'],
                                   case_info['raw']['family_id'])

    chanjo_db = apps.coverage.Coverage(context.obj)
    coverage_query = chanjo_db.validate(case_id)

    results = Counter()
    for data in coverage_query:
        sample_id = data.Sample.id
        log.info("validating sample: %s", sample_id)
        if lims_data[sample_id]['is_external']:
            log.info("external sample, skipping quality checks")
            results.update(['SKIP'])
            continue
        elif lims_data[sample_id]['is_panel']:
            log.debug("TGA sample")
            if lims_data[sample_id]['reads'] >= 75e6 and data.completeness_10 < 0.96:
                log.error("completeness too low: %s < 0.96", data.completeness_10)
                results.update(['FAIL'])
            elif lims_data[sample_id]['reads'] >= 30e6 and data.completeness_10 < 0.95:
                log.error("completeness too low: %s < 0.95", data.completeness_10)
                results.update(['FAIL'])
            elif data.completeness_10 < 0.8:
                log.error("completeness too low: %s < 0.8", data.completeness_10)
                results.update(['FAIL'])
            else:
                log.info('coverage OK!')
                results.update(['PASS'])
        else:
            log.debug('WGS sample')
            if lims_data[sample_id]['is_low_input'] and data.mean_coverage < 22.5:
                log.debug('low input sample')
                log.error("mean coverage too low: %s < 22.5", data.mean_coverage)
                results.update(['FAIL'])
            elif data.mean_coverage < 26:
                log.error("mean coverage too low: %s < 26", data.mean_coverage)
                results.update(['FAIL'])
            else:
                log.info('coverage OK!')
                results.update(['PASS'])

    samples_no = len(lims_data)
    skipped_no = results['SKIP'] or 0
    if skipped_no > 0:
        log.warn("skipped %s/%s samples", results['SKIP'] or 0, samples_no)

    log.info("passed %s/%s samples", results['PASS'] or 0, samples_no)

    failed_no = results['FAIL'] or 0
    if failed_no > 0:
        log.error("failed %s/%s samples", results['FAIL'] or 0, samples_no)
        context.abort()
