# -*- coding: utf-8 -*-
import datetime as dt
import logging
import sys

import click

from cg.store import Store
from cg.apps import coverage as coverage_app, gt, hk, loqus, tb, scoutapi, beacon as beacon_app, \
    lims
from cg.exc import DuplicateRecordError
from cg.meta.upload.coverage import UploadCoverageApi
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.meta.upload.observations import UploadObservationsAPI
from cg.meta.upload.scoutapi import UploadScoutAPI
from cg.meta.upload.beacon import UploadBeaconApi
from cg.meta.analysis import AnalysisAPI
from cg.meta.deliver.api import DeliverAPI
from cg.meta.report.api import ReportAPI

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option('-f', '--family', 'family_id', help='Upload to all apps')
@click.pass_context
def upload(context, family_id):
    """Upload results from analyses."""

    click.echo(click.style('----------------- UPLOAD ----------------------'))
        
    context.obj['status'] = Store(context.obj['database'])
    context.obj['housekeeper_api'] = hk.HousekeeperAPI(context.obj)

    context.obj['lims_api'] = lims.LimsAPI(context.obj)
    context.obj['tb_api'] = tb.TrailblazerAPI(context.obj)
    context.obj['chanjo_api'] = coverage_app.ChanjoAPI(context.obj)
    context.obj['deliver_api'] = DeliverAPI(context.obj, hk_api=context.obj['housekeeper_api'],
                                            lims_api=context.obj['lims_api'])
    context.obj['scout_api'] = scoutapi.ScoutAPI(context.obj)
    context.obj['analysis_api'] = AnalysisAPI(context.obj, hk_api=context.obj['housekeeper_api'],
                                              scout_api=context.obj['scout_api'],
                                              tb_api=context.obj[
                                                  'tb_api'],
                                              lims_api=context.obj['lims_api'],
                                              deliver_api=context.obj['deliver_api'])
    context.obj['report_api'] = ReportAPI(
        db=context.obj['status'],
        lims_api=context.obj['lims_api'],
        chanjo_api=context.obj['chanjo_api'],
        analysis_api=context.obj['analysis_api'],
        scout_api=context.obj['scout_api']
    )

    context.obj['scout_upload_api'] = UploadScoutAPI(
        status_api=context.obj['status'],
        hk_api=context.obj['housekeeper_api'],
        scout_api=context.obj['scout_api'],
        madeline_exe=context.obj['madeline_exe'],
        analysis_api=context.obj['analysis_api']
    )

    if family_id:
        family_obj = context.obj['status'].family(family_id)
        analysis_obj = family_obj.analyses[0]
        if analysis_obj.uploaded_at is not None:
            message = f"analysis already uploaded: {analysis_obj.uploaded_at.date()}"
            click.echo(click.style(message, fg='yellow'))
        else:
            context.invoke(coverage, re_upload=True, family_id=family_id)
            context.invoke(validate, family_id=family_id)
            context.invoke(genotypes, re_upload=False, family_id=family_id)
            context.invoke(observations, family_id=family_id)
            context.invoke(delivery_report, family_id=family_id,
                           customer_id=family_obj.customer.internal_id)
            context.invoke(scout, family_id=family_id)
            analysis_obj.uploaded_at = dt.datetime.now()
            context.obj['status'].commit()
            click.echo(click.style(f"{family_id}: analysis uploaded!", fg='green'))


@upload.command('delivery-report')
@click.argument('customer_id')
@click.argument('family_id')
@click.option('-p', '--print', 'print_console', is_flag=True, help='print report to console')
@click.pass_context
def delivery_report(context, customer_id, family_id, print_console):
    """Generate a delivery report for a case.

    The report contains data from several sources:

    status-db:
        family
        customer_obj
        application_objs
        accredited
        panels
        samples
        sample.id
        sample.status
        sample.ticket
        sample.million_read_pairs

    lims:
        sample.name
        sample.sex
        sample.source
        sample.application
        sample.received
        sample.prep_method
        sample.sequencing_method
        sample.delivery_method
        sample.delivery_date
        sample.processing_time

    trailblazer:
        sample.mapped_reads
        sample.duplicates
        sample.analysis_sex
        mip_version
        genome_build

    chanjo:
        sample.target_coverage
        sample.target_completeness

    scout:
        panel-genes

    today:
        generated upon report creation

    """

    click.echo(click.style('----------------- DELIVERY_REPORT -------------'))

    report_api = context.obj['report_api']

    if print_console:
        delivery_report_html = report_api.create_delivery_report(customer_id, family_id)

        click.echo(delivery_report_html)
    else:
        tb_api = context.obj['tb_api']
        delivery_report_file = report_api.create_delivery_report_file(customer_id, family_id,
                                                                      file_path=
                                                                      tb_api.get_family_root_dir(
                                                                        family_id))
        hk_api = context.obj['housekeeper_api']
        _add_delivery_report_to_hk(delivery_report_file, hk_api, family_id)


def _add_delivery_report_to_hk(delivery_report_file, hk_api: hk.HousekeeperAPI, family_id):
    delivery_report_tag_name = 'delivery-report'
    version_obj = hk_api.last_version(family_id)
    uploaded_delivery_report_files = hk_api.get_files(bundle=family_id,
                                                      tags=[delivery_report_tag_name])
    number_of_delivery_reports = len(uploaded_delivery_report_files.all())
    is_bundle_missing_delivery_report = number_of_delivery_reports == 0

    if is_bundle_missing_delivery_report:
        file_obj = hk_api.add_file(delivery_report_file.name, version_obj, delivery_report_tag_name)
        hk_api.include_file(file_obj, version_obj)
        hk_api.add_commit(file_obj)


@upload.command()
@click.option('-r', '--re-upload', is_flag=True, help='re-upload existing analysis')
@click.argument('family_id')
@click.pass_context
def coverage(context, re_upload, family_id):
    """Upload coverage from an analysis to Chanjo."""

    click.echo(click.style('----------------- COVERAGE --------------------'))

    chanjo_api = coverage_app.ChanjoAPI(context.obj)
    family_obj = context.obj['status'].family(family_id)
    api = UploadCoverageApi(context.obj['status'], context.obj['housekeeper_api'], chanjo_api)
    coverage_data = api.data(family_obj.analyses[0])
    api.upload(coverage_data, replace=re_upload)


@upload.command()
@click.option('-r', '--re-upload', is_flag=True, help='re-upload existing analysis')
@click.argument('family_id')
@click.pass_context
def genotypes(context, re_upload, family_id):
    """Upload genotypes from an analysis to Genotype."""

    click.echo(click.style('----------------- GENOTYPES -------------------'))

    tb_api = tb.TrailblazerAPI(context.obj)
    gt_api = gt.GenotypeAPI(context.obj)
    family_obj = context.obj['status'].family(family_id)
    api = UploadGenotypesAPI(context.obj['status'], context.obj['housekeeper_api'], tb_api, gt_api)
    results = api.data(family_obj.analyses[0])
    if results:
        api.upload(results, replace=re_upload)


@upload.command()
@click.argument('family_id')
@click.pass_context
def observations(context, family_id):
    """Upload observations from an analysis to LoqusDB."""

    click.echo(click.style('----------------- OBSERVATIONS ----------------'))

    loqus_api = loqus.LoqusdbAPI(context.obj)
    family_obj = context.obj['status'].family(family_id)

    if family_obj.customer.loqus_upload == True:
        api = UploadObservationsAPI(context.obj['status'], context.obj['housekeeper_api'], loqus_api)
        try:
            api.process(family_obj.analyses[0])
            click.echo(click.style(f"{family_id}: observations uploaded!", fg='green'))
        except DuplicateRecordError as error:
            LOG.info(f"skipping observations upload: {error.message}")
    else:
        click.echo(click.style(f"{family_id}: {family_obj.customer.internal_id} not whitelisted for upload to loqusdb. Skipping!", fg='yellow'))


@upload.command()
@click.option('-r', '--re-upload', is_flag=True, help='re-upload existing analysis')
@click.option('-p', '--print', 'print_console', is_flag=True, help='print config values')
@click.argument('family_id')
@click.pass_context
def scout(context, re_upload, print_console, family_id):
    """Upload variants from analysis to Scout."""

    click.echo(click.style('----------------- SCOUT -----------------------'))

    scout_api = scoutapi.ScoutAPI(context.obj)
    family_obj = context.obj['status'].family(family_id)
    scout_upload_api = context.obj['scout_upload_api']
    scout_config = scout_upload_api.generate_config(family_obj.analyses[0])
    if print_console:
        click.echo(scout_config)
    else:
        scout_api.upload(scout_config, force=re_upload)


@upload.command()
@click.argument('family_id')
@click.option('-p', '--panel', help='Gene panel to filter VCF by', required=True, multiple=True)
@click.option('-out', '--outfile', help='Name of pdf outfile', default=None)
@click.option('-cust', '--customer', help='Name of customer', default="")
@click.option('-qual', '--quality', help='Variant quality threshold', default=20)
@click.option('-ref', '--genome_reference', help='Chromosome build (default=grch37)',
              default="grch37")
@click.pass_context
def beacon(context: click.Context, family_id: str, panel: str, outfile: str, customer: str,
           quality: int, genome_reference: str):
    """Upload variants for affected samples in a family to cgbeacon."""

    click.echo(click.style('----------------- BEACON ----------------------'))

    if outfile:
        outfile += dt.datetime.now().strftime("%Y-%m-%d_%H:%M:%S.pdf")
    api = UploadBeaconApi(
        status=context.obj['status'],
        hk_api=context.obj['housekeeper_api'],
        scout_api=scoutapi.ScoutAPI(context.obj),
        beacon_api=beacon_app.BeaconApi(context.obj),
    )
    api.upload(
        family_id=family_id,
        panel=panel,
        outfile=outfile,
        customer=customer,
        qual=quality,
        reference=genome_reference,
    )


@upload.command()
@click.pass_context
def auto(context):
    """Upload all completed analyses."""

    click.echo(click.style('----------------- AUTO ------------------------'))

    exit_code = 0
    for analysis_obj in context.obj['status'].analyses_to_upload():
        LOG.info(f"uploading family: {analysis_obj.family.internal_id}")
        try:
            context.invoke(upload, family_id=analysis_obj.family.internal_id)
        except Exception as e:
            import traceback
            LOG.error(f"uploading family failed: {analysis_obj.family.internal_id}")
            LOG.error(traceback.format_exc())
            exit_code = 1

    sys.exit(exit_code)


@upload.command()
@click.argument('family_id')
@click.pass_context
def validate(context, family_id):
    """Validate a family of samples."""

    click.echo(click.style('----------------- VALIDATE --------------------'))

    family_obj = context.obj['status'].family(family_id)
    chanjo_api = coverage_app.ChanjoAPI(context.obj)
    chanjo_samples = []
    for link_obj in family_obj.links:
        sample_id = link_obj.sample.internal_id
        chanjo_sample = chanjo_api.sample(sample_id)
        if chanjo_sample is None:
            click.echo(click.style(f"upload coverage for {sample_id}", fg='yellow'))
            continue
        chanjo_samples.append(chanjo_sample)
    if chanjo_samples:
        coverage_results = chanjo_api.omim_coverage(chanjo_samples)
        for link_obj in family_obj.links:
            sample_id = link_obj.sample.internal_id
            if sample_id in coverage_results:
                completeness = coverage_results[sample_id]['mean_completeness']
                mean_coverage = coverage_results[sample_id]['mean_coverage']
                click.echo(f"{sample_id}: {mean_coverage:.2f}X - {completeness:.2f}%")
            else:
                click.echo(f"{sample_id}: sample not found in chanjo", color='yellow')
