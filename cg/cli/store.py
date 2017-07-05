# -*- coding: utf-8 -*-
import click

from cg.apps import hk, tb
from cg.exc import AnalysisNotFinishedError


@click.command()
@click.argument('config_stream', type=click.File('r'))
@click.pass_context
def store(context, config_stream):
    """Store a finished analysis in Housekeeper."""
    tb_api = tb.TrailblazerAPI(context.obj)
    hk_api = hk.HousekeeperAPI(context.obj)

    try:
        bundle_data = tb_api.add_analysis(config_stream)
    except AnalysisNotFinishedError as error:
        click.echo(click.style(error.message, fg='red'))
        context.abort()

    new_bundle = hk_api.add_bundle(bundle_data)
    hk_api.add_commit(new_bundle)
    new_version = new_bundle.versions[0]
    click.echo(f"new bundle added: {new_bundle.name}, version {new_version.id}")
