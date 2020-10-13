import logging
import click
from cg.apps.tb import TrailblazerAPI
from cg.exc import TrailblazerAPIHTTPError

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
    if analysis_obj:
        LOG.info(f"Found {analysis_obj.to_dict()}")
    LOG.info(f"No analyses for {case_id} found!")


@trailblazer.command("mark-analyses-deleted")
@click.argument("case_id", type=str)
@click.pass_context
def mark_analyses_deleted(context, case_id):
    analyses = context.obj["trailblazer_api"].mark_analyses_deleted(case_id=case_id)
    LOG.info(
        f"Marked deleted analyses for case {case_id}: {[analysis.id for analysis in analyses]}"
    )


@trailblazer.command("add-pending-analysis")
@click.argument("case_id", type=str)
@click.argument("email", type=str)
@click.pass_context
def add_pending_analysis(context, case_id, email):
    analysis_obj = context.obj["trailblazer_api"].add_pending_analysis(case_id=case_id, email=email)
    LOG.info(f"Created pending analysis {analysis_obj.to_dict()}")


@trailblazer.command("delete-analysis")
@click.option("--force", is_flag=True)
@click.argument("case_id", type=str)
@click.pass_context
def delete_analysis(context, case_id, force):
    try:
        analysis_obj = context.obj["trailblazer_api"].delete_analysis(case_id=case_id, force=force)
        LOG.info(f"Deleted analysis directory for {case_id}: {analysis_obj.out_dir.parent}")
    except TrailblazerAPIHTTPError as e:
        LOG.info(f"Did not delete analysis directory: {e.message}")
