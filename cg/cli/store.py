# -*- coding: utf-8 -*-
import click

from cg.apps import hk, tb
from cg.exc import AnalysisNotFinishedError
from cg.store import Store


@click.command()
@click.argument('config_stream', type=click.File('r'))
@click.pass_context
def store(context, config_stream):
    """Store a finished analysis in Housekeeper."""
    status_api = Store(context.obj['database'])
    tb_api = tb.TrailblazerAPI(context.obj)
    hk_api = hk.HousekeeperAPI(context.obj)

    # gather files and bundle in Housekeeper
    try:
        bundle_data = tb_api.add_analysis(config_stream)
    except AnalysisNotFinishedError as error:
        click.echo(click.style(error.message, fg='red'))
        context.abort()
    new_bundle = hk_api.add_bundle(bundle_data)
    new_version = new_bundle.versions[0]

    # add new analysis to the status API
    family_obj = status_api.family(new_bundle.name)
    new_analysis = status_api.add_analysis(
        family=family_obj,
        pipeline='mip',
        version=bundle_data['pipeline_version'],
        analyzed=new_version.created_at,
        primary=(len(family_obj.analyses) == 0),
    )
    version_date = new_version.created_at.date()
    click.echo(f"new bundle added: {new_bundle.name}, version {version_date}")

    # include the files in the housekeeper system
    try:
        hk_api.include(new_version)
    except hk.VersionIncludedError as error:
        click.echo(click.style(error.message, fg='red'))
        context.abort()

    hk_api.add_commit(new_bundle)
    status_api.add_commit(new_analysis)
    click.echo(click.style('included files in Housekeeper', fg='green'))
