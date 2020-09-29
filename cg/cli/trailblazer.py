import logging
import click
from cg.apps.tb import TrailblazerAPI

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def trailblazer(context):
    """Trailblazer context"""
    context.obj["trailblazer_api"] = TrailblazerAPI(context.obj)


@trailblazer.command("analysis")
@click.argument("analysis_id", type=int)
@click.pass_context
def analysis(context, analysis_id: int):
    context.obj["trailblazer_api"].get_analysis(analysis_id=analysis_id)


@trailblazer.command("analyses")
@click.pass_context
def analyses(context, analysis_id: int):
    context.obj["trailblazer_api"].get_analysis(analysis_id=analysis_id)
