import logging
import click
from cg.apps.tb import TrailblazerAPI

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def trailblazer(context):
    """Trailblazer context"""
    context.obj["trailblazer_api"] = TrailblazerAPI(context.obj)


@trailblazer.command("get-latest-analysis")
@click.argument("case_id", type=str)
@click.pass_context
def get_latest_analysis(context, case_id):
    analysis_obj = context.obj["trailblazer_api"].get_latest_analysis(case_id=case_id)
    LOG.info(f"Found {analysis_obj}")


@trailblazer.command("mark-analyses-deleted")
@click.argument("case_id", type=str)
@click.pass_context
def mark_analyses_deleted(context, case_id):
    analyses = context.obj["trailblazer_api"].mark_analyses_deleted(case_id=case_id)
    LOG.info(f"Marked deleted {analyses}")
