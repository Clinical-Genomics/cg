"""CLI support to create config and/or start TOMTE."""

import logging
import click

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def tomte(context: click.Context) -> None:
    """gms/tomte analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis[MetaApis.ANALYSIS_API] = TomteAnalysisAPI(config=context.obj)
