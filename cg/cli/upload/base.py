"""Code that handles CLI commands to upload"""
import datetime as dt
import logging
import sys
import traceback

import click


from cg.constants import Pipeline
from cg.exc import AnalysisUploadError, CgError
from cg.meta.report.api import ReportAPI
from cg.meta.upload.scout.scoutapi import UploadScoutAPI
from cg.store import models
from cg.utils.click.EnumChoice import EnumChoice

from .coverage import coverage
from .delivery_report import delivery_report, delivery_report_to_scout, delivery_reports
from .genotype import genotypes
from .mutacc import process_solved, processed_solved
from .observations import observations
from .scout import create_scout_load_config, scout, upload_case_to_scout
from .utils import suggest_cases_to_upload
from .validate import validate
from ...meta.workflow.mip_dna import MipDNAAnalysisAPI

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option("-f", "--family", "family_id", help="Upload to all apps")
@click.option(
    "-r",
    "--restart",
    "force_restart",
    is_flag=True,
    help="Force upload of analysis " "marked as started",
)
@click.pass_context
def upload(context, family_id, force_restart):
    """Upload results from analyses."""

    if not context.obj.get("analysis_api"):
        context.obj["analysis_api"] = MipDNAAnalysisAPI(context.obj)
    analysis_api = context.obj["analysis_api"]

    click.echo(click.style("----------------- UPLOAD ----------------------"))

    if family_id:
        try:
            analysis_api.verify_case_id_in_statusdb(case_id=family_id)
        except CgError:
            raise context.abort()

        case_obj = analysis_api.status_db.family(family_id)
        if not case_obj.analyses:
            message = f"no analysis exists for family: {family_id}"
            click.echo(click.style(message, fg="red"))
            context.abort()

        analysis_obj = case_obj.analyses[0]

        if analysis_obj.uploaded_at is not None:
            message = f"analysis already uploaded: {analysis_obj.uploaded_at.date()}"
            click.echo(click.style(message, fg="red"))
            context.abort()

        if not force_restart and analysis_obj.upload_started_at is not None:
            if dt.datetime.now() - analysis_obj.upload_started_at > dt.timedelta(hours=24):
                raise AnalysisUploadError(
                    f"The upload started at {analysis_obj.upload_started_at} "
                    f"something went wrong, restart it with the --restart flag"
                )

            message = f"analysis upload already started: {analysis_obj.upload_started_at.date()}"
            click.echo(click.style(message, fg="yellow"))
            return

    context.obj["report_api"] = ReportAPI(
        store=analysis_api.status_db,
        lims_api=analysis_api.lims_api,
        chanjo_api=analysis_api.chanjo_api,
        analysis_api=analysis_api,
        scout_api=analysis_api.scout_api,
    )

    context.obj["scout_upload_api"] = UploadScoutAPI(
        hk_api=analysis_api.housekeeper_api,
        scout_api=analysis_api.scout_api,
        madeline_api=analysis_api.madeline_api,
        analysis_api=analysis_api,
        lims_api=analysis_api.lims_api,
    )

    if context.invoked_subcommand is not None:
        return

    if not family_id:
        suggest_cases_to_upload(context)
        context.abort()

    case_obj: models.Family = analysis_api.status_db.family(family_id)
    analysis_obj: models.Analysis = case_obj.analyses[0]
    if analysis_obj.uploaded_at is not None:
        message = f"analysis already uploaded: {analysis_obj.uploaded_at.date()}"
        click.echo(click.style(message, fg="yellow"))
    else:
        analysis_obj.upload_started_at = dt.datetime.now()
        analysis_api.status_db.commit()
        context.invoke(coverage, re_upload=True, family_id=family_id)
        context.invoke(validate, family_id=family_id)
        context.invoke(genotypes, re_upload=False, family_id=family_id)
        context.invoke(observations, case_id=family_id)
        context.invoke(scout, case_id=family_id)
        analysis_obj.uploaded_at = dt.datetime.now()
        analysis_api.status_db.commit()
        click.echo(click.style(f"{family_id}: analysis uploaded!", fg="green"))


@upload.command()
@click.option("--pipeline", type=EnumChoice(Pipeline), help="Limit to specific pipeline")
@click.pass_context
def auto(context: click.Context, pipeline: Pipeline = None):
    """Upload all completed analyses."""

    if not context.obj.get("analysis_api"):
        context.obj["analysis_api"] = MipDNAAnalysisAPI(context.obj)
    analysis_api = context.obj["analysis_api"]

    click.echo(click.style("----------------- AUTO ------------------------"))

    exit_code = 0
    for analysis_obj in analysis_api.status_db.analyses_to_upload(pipeline=pipeline):

        if analysis_obj.family.analyses[0].uploaded_at is not None:
            LOG.warning(
                "Newer analysis already uploaded for %s, skipping",
                analysis_obj.family.internal_id,
            )
            continue
        internal_id = analysis_obj.family.internal_id

        LOG.info("Uploading family: %s", internal_id)
        try:
            context.invoke(upload, family_id=internal_id)
        except Exception:
            LOG.error("Uploading family failed: %s", internal_id)
            LOG.error(traceback.format_exc())
            exit_code = 1

    sys.exit(exit_code)


upload.add_command(process_solved)
upload.add_command(processed_solved)
upload.add_command(validate)
upload.add_command(scout)
upload.add_command(upload_case_to_scout)
upload.add_command(create_scout_load_config)
upload.add_command(observations)
upload.add_command(genotypes)
upload.add_command(coverage)
upload.add_command(delivery_report)
upload.add_command(delivery_reports)
upload.add_command(delivery_report_to_scout)
