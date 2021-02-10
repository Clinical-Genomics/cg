"""Code that handles CLI commands to upload"""
import datetime as dt
import logging
import sys
import traceback

import click
from cg.apps.coverage import ChanjoAPI
from cg.apps.gt import GenotypeAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import Pipeline
from cg.exc import AnalysisUploadError
from cg.meta.report.api import ReportAPI
from cg.meta.upload.scout.scoutapi import UploadScoutAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.store import Store
from cg.utils.click.EnumChoice import EnumChoice

from .coverage import coverage
from .delivery_report import delivery_report, delivery_report_to_scout, delivery_reports
from .genotype import genotypes
from .mutacc import process_solved, processed_solved
from .observations import observations
from .scout import create_scout_load_config, scout, upload_case_to_scout
from .utils import suggest_cases_to_upload
from .validate import validate

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

    click.echo(click.style("----------------- UPLOAD ----------------------"))

    context.obj["status_db"] = Store(context.obj["database"])

    if family_id:
        case_obj = context.obj["status_db"].family(family_id)
        if not case_obj:
            message = f"family not found: {family_id}"
            click.echo(click.style(message, fg="red"))
            context.abort()

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

    context.obj["housekeeper_api"] = HousekeeperAPI(context.obj)
    context.obj["madeline_api"] = MadelineAPI(context.obj)
    context.obj["genotype_api"] = GenotypeAPI(context.obj)
    context.obj["lims_api"] = LimsAPI(context.obj)
    context.obj["trailblazer_api"] = TrailblazerAPI(context.obj)
    context.obj["chanjo_api"] = ChanjoAPI(context.obj)
    context.obj["scout_api"] = ScoutAPI(context.obj)

    context.obj["analysis_api"] = MipAnalysisAPI(
        db=context.obj["status_db"],
        hk_api=context.obj["housekeeper_api"],
        tb_api=context.obj["trailblazer_api"],
        scout_api=context.obj["scout_api"],
        lims_api=context.obj["lims_api"],
        script=context.obj["mip-rd-dna"]["script"],
        pipeline=context.obj["mip-rd-dna"]["pipeline"],
        conda_env=context.obj["mip-rd-dna"]["conda_env"],
        root=context.obj["mip-rd-dna"]["root"],
    )
    context.obj["report_api"] = ReportAPI(
        store=context.obj["status_db"],
        lims_api=context.obj["lims_api"],
        chanjo_api=context.obj["chanjo_api"],
        analysis_api=context.obj["analysis_api"],
        scout_api=context.obj["scout_api"],
    )

    context.obj["scout_upload_api"] = UploadScoutAPI(
        hk_api=context.obj["housekeeper_api"],
        scout_api=context.obj["scout_api"],
        madeline_api=context.obj["madeline_api"],
        analysis_api=context.obj["analysis_api"],
        lims_api=context.obj["lims_api"],
    )

    if context.invoked_subcommand is not None:
        return

    if not family_id:
        suggest_cases_to_upload(context)
        context.abort()

    case_obj = context.obj["status_db"].family(family_id)
    analysis_obj = case_obj.analyses[0]
    if analysis_obj.uploaded_at is not None:
        message = f"analysis already uploaded: {analysis_obj.uploaded_at.date()}"
        click.echo(click.style(message, fg="yellow"))
    else:
        analysis_obj.upload_started_at = dt.datetime.now()
        context.obj["status_db"].commit()
        context.invoke(coverage, re_upload=True, family_id=family_id)
        context.invoke(validate, family_id=family_id)
        context.invoke(genotypes, re_upload=False, family_id=family_id)
        context.invoke(observations, case_id=family_id)
        context.invoke(scout, case_id=family_id)
        analysis_obj.uploaded_at = dt.datetime.now()
        context.obj["status_db"].commit()
        click.echo(click.style(f"{family_id}: analysis uploaded!", fg="green"))


@upload.command()
@click.option("--pipeline", type=EnumChoice(Pipeline), help="Limit to specific pipeline")
@click.pass_context
def auto(context: click.Context, pipeline: Pipeline = None):
    """Upload all completed analyses."""

    click.echo(click.style("----------------- AUTO ------------------------"))

    exit_code = 0
    for analysis_obj in context.obj["status_db"].analyses_to_upload(pipeline=pipeline):

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
