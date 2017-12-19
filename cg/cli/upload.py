# -*- coding: utf-8 -*-
import datetime as dt
import logging

import click

from cg.store import Store
from cg.apps import coverage as coverage_app, gt, hk, loqus, tb, scoutapi, beacon as beacon_app
from cg.exc import DuplicateRecordError
from cg.meta.upload.coverage import UploadCoverageApi
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.meta.upload.observations import UploadObservationsAPI
from cg.meta.upload.scoutapi import UploadScoutAPI
from cg.meta.upload.beacon import UploadBeaconApi

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option('-f', '--family', 'family_id', help='Upload to all apps')
@click.pass_context
def upload(context, family_id):
    """Upload results from analyses."""
    context.obj['status'] = Store(context.obj['database'])
    context.obj['housekeeper_api'] = hk.HousekeeperAPI(context.obj)
    if family_id:
        family_obj = context.obj['status'].family(family_id)
        analysis_obj = family_obj.analyses[0]
        if analysis_obj.uploaded_at is not None:
            message = f"analysis already uploaded: {analysis_obj.uploaded_at.date()}"
            click.echo(click.style(message, fg='yellow'))
            context.abort()

        context.invoke(coverage, family_id=family_id)
        context.invoke(validate, family_id=family_id)
        context.invoke(genotypes, family_id=family_id)
        context.invoke(observations, family_id=family_id)
        context.invoke(scout, family_id=family_id)

        analysis_obj.uploaded_at = dt.datetime.now()
        context.obj['status'].commit()
        click.echo(click.style(f"{family_id}: analysis uploaded!", fg='green'))


@upload.command()
@click.option('-r', '--re-upload', is_flag=True, help='re-upload existing analysis')
@click.argument('family_id')
@click.pass_context
def coverage(context, re_upload, family_id):
    """Upload coverage from an analysis to Chanjo."""
    chanjo_api = coverage_app.ChanjoAPI(context.obj)
    family_obj = context.obj['status'].family(family_id)
    api = UploadCoverageApi(context.obj['status'], context.obj['housekeeper_api'], chanjo_api)
    coverage_data = api.data(family_obj.analyses[0])
    api.upload(coverage_data, replace=re_upload)


@upload.command()
@click.argument('family_id')
@click.pass_context
def genotypes(context, family_id):
    """Upload genotypes from an analysis to Genotype."""
    tb_api = tb.TrailblazerAPI(context.obj)
    gt_api = gt.GenotypeAPI(context.obj)
    family_obj = context.obj['status'].family(family_id)
    api = UploadGenotypesAPI(context.obj['status'], context.obj['housekeeper_api'], tb_api, gt_api)
    results = api.data(family_obj.analyses[0])
    if results:
        api.upload(results)


@upload.command()
@click.argument('family_id')
@click.pass_context
def observations(context, family_id):
    """Upload observations from an analysis to LoqusDB."""
    loqus_api = loqus.LoqusdbAPI(context.obj)
    family_obj = context.obj['status'].family(family_id)
    api = UploadObservationsAPI(context.obj['status'], context.obj['housekeeper_api'], loqus_api)
    try:
        api.process(family_obj.analyses[0])
        click.echo(click.style(f"{family_id}: observations uploaded!", fg='green'))
    except DuplicateRecordError as error:
        LOG.info(f"skipping observations upload: {error.message}")


@upload.command()
@click.option('-r', '--re-upload', is_flag=True, help='re-upload existing analysis')
@click.option('-p', '--print', 'print_console', is_flag=True, help='print config values')
@click.argument('family_id')
@click.pass_context
def scout(context, re_upload, print_console, family_id):
    """Upload variants from analysis to Scout."""
    scout_api = scoutapi.ScoutAPI(context.obj)
    family_obj = context.obj['status'].family(family_id)
    api = UploadScoutAPI(
        status_api=context.obj['status'],
        hk_api=context.obj['housekeeper_api'],
        scout_api=scout_api,
        madeline_exe=context.obj['madeline_exe'],
    )
    results = api.data(family_obj.analyses[0])
    if print_console:
        print(results)
    else:
        scout_api.upload(results, force=re_upload)


@upload.command()
@click.argument('family_id')
@click.option('-p', '--panel', help='Gene panel to filter VCF by', required=True)
@click.option('-out', '--outfile', help='Path to PDF report outfile', default="cgbeacon")
@click.option('-cust', '--customer', help='Name of customer', default="")
@click.option('-qual', '--quality', help='Variant quality threhold', default=20)
@click.option('-ref', '--genome_reference', help='Chromosome build (default=grch37)', default="grch37")
@click.pass_context
def beacon(context: click.Context, family_id: str, panel: str, outfile: str, customer: str, quality: int, genome_reference: str):
    """Upload variants for affected samples in a family to cgbeacon."""
    outfile +=  dt.datetime.now().strftime("%Y-%m-%d_%H:%M:%S.pdf")
    api = UploadBeaconApi(
        status=context.obj['status'],
        hk_api=context.obj['housekeeper_api'],
        scout_api=scoutapi.ScoutAPI(context.obj),
        beacon_api=beacon_app.BeaconApi(context.obj),
    )
    result = api.upload(
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
    for analysis_obj in context.obj['status'].analyses_to_upload():
        LOG.info(f"uploading family: {analysis_obj.family.internal_id}")
        try:
            context.invoke(upload, family_id=analysis_obj.family.internal_id)
        except Exception as e:
            import traceback
            LOG.error(f"uploading family failed: {analysis_obj.family.internal_id}")
            LOG.error(traceback.format_exc())


@upload.command()
@click.argument('family_id')
@click.pass_context
def validate(context, family_id):
    """Validate a family of samples."""
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
                print(f"{sample_id}: sample not found in chanjo")
