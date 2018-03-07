# -*- coding: utf-8 -*-
import datetime as dt
import logging
from pathlib import Path

import click

from cg.apps import hk, tb
from cg.meta import report
from cg.exc import AnalysisNotFinishedError
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def store(context):
    """Store results from MIP in housekeeper."""
    context.obj['db'] = Store(context.obj['database'])
    context.obj['tb_api'] = tb.TrailblazerAPI(context.obj)
    context.obj['hk_api'] = hk.HousekeeperAPI(context.obj)
    context.obj['report_api'] = report.ReportAPI(context.obj)


@store.command()
@click.argument('config_stream', type=click.File('r'))
@click.pass_context
def analysis(context, config_stream):
    """Store a finished analysis in Housekeeper."""
    status = context.obj['db']
    tb_api = context.obj['tb_api']
    hk_api = context.obj['hk_api']
    report_api = context.obj['report_api']

    new_analysis = _gather_files_and_bundle_in_housekeeper(config_stream, context, hk_api,
                                                           report_api, status, tb_api)

    status.add_commit(new_analysis)
    click.echo(click.style('included files in Housekeeper', fg='green'))


def _gather_files_and_bundle_in_housekeeper(config_stream, context, hk_api, report_api, status,
                                            tb_api):
    try:
        bundle_data = tb_api.add_analysis(config_stream)
    except AnalysisNotFinishedError as error:
        click.echo(click.style(error.message, fg='red'))
        context.abort()
    try:
        results = hk_api.add_bundle(bundle_data)
        if results is None:
            print(click.style('analysis version already added', fg='yellow'))
            context.abort()
        bundle_obj, version_obj = results
        version_obj.bundle = bundle_obj
    except FileNotFoundError as error:
        click.echo(click.style(f"missing file: {error.args[0]}", fg='red'))
        context.abort()
    family_obj = _add_new_analysis_to_the_status_API(bundle_obj, status)
    _reset_the_action_on_the_family_from_running(family_obj)
    new_analysis = _add_new_complete_analysis_record(bundle_data, family_obj, status, version_obj)
    delivery_report_file = report_api.create_temporary_delivery_report_file(
        customer_id=family_obj.customer_id, family_id=family_obj.name)
    _add_report_to_hk(delivery_report_file, hk_api, status, version_obj)
    version_date = version_obj.created_at.date()
    click.echo(f"new bundle added: {bundle_obj.name}, version {version_date}")
    _include_the_files_in_the_housekeeper_system(bundle_obj, context, hk_api, version_obj)
    return new_analysis


def _add_report_to_hk(delivery_report_file, hk_api, version_obj):
    tag_name = 'DELIVERY-REPORT'    # CHANGE!
    new_file = hk_api.new_file(
        path=str(Path(delivery_report_file).absolute()),
        to_archive=False,
        tags=[hk_api.tag(tag_name)]
    )
    new_file.version = version_obj
    hk_api.add_commit(new_file)


def _include_the_files_in_the_housekeeper_system(bundle_obj, context, hk_api, version_obj):
    try:
        hk_api.include(version_obj)
    except hk.VersionIncludedError as error:
        click.echo(click.style(error.message, fg='red'))
        context.abort()
    hk_api.add_commit(bundle_obj, version_obj)


def _add_new_complete_analysis_record(bundle_data, family_obj, status, version_obj):
    new_analysis = status.add_analysis(
        pipeline='mip',
        version=bundle_data['pipeline_version'],
        started_at=version_obj.created_at,
        completed_at=dt.datetime.now(),
        primary=(len(family_obj.analyses) == 0),
    )
    new_analysis.family = family_obj
    return new_analysis


def _reset_the_action_on_the_family_from_running(family_obj):
    family_obj.action = None


def _add_new_analysis_to_the_status_API(bundle_obj, status):
    family_obj = status.family(bundle_obj.name)
    return family_obj


@store.command()
@click.pass_context
def completed(context):
    """Store all completed analyses."""
    hk_api = context.obj['hk_api']
    for analysis_obj in context.obj['tb_api'].analyses(status='completed', deleted=False):
        existing_record = hk_api.version(analysis_obj.family, analysis_obj.started_at)
        if existing_record:
            LOG.debug(f"analysis stored: {analysis_obj.family} - {analysis_obj.started_at}")
            continue
        click.echo(click.style(f"storing family: {analysis_obj.family}", fg='blue'))
        with Path(analysis_obj.config_path).open() as config_stream:
            context.invoke(analysis, config_stream=config_stream)
