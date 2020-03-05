# -*- coding: utf-8 -*-
import logging

import ruamel.yaml
import click
from dateutil.parser import parse as parse_date
from datetime import datetime

from pathlib import Path

from cg.apps import tb, hk, scoutapi, beacon as beacon_app
from cg.meta.upload.beacon import UploadBeaconApi
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def clean(context):
    """Remove stuff."""
    context.obj["db"] = Store(context.obj["database"])
    context.obj["tb"] = tb.TrailblazerAPI(context.obj)
    context.obj["hk"] = hk.HousekeeperAPI(context.obj)
    context.obj["scout"] = scoutapi.ScoutAPI(context.obj)
    context.obj["beacon"] = beacon_app.BeaconApi(context.obj)


@clean.command()
@click.option(
    "-type",
    "--item_type",
    type=click.Choice(["family", "sample"]),
    required=True,
    help="family/sample to remove from beacon",
)
@click.argument("item_id", type=click.STRING)
@click.pass_context
def beacon(context: click.Context, item_type, item_id):
    """Remove beacon for a sample or one or more affected samples from a family."""
    LOG.info("Removing beacon vars for %s %s", item_type, item_id)
    api = UploadBeaconApi(
        status=context.obj["db"],
        hk_api=context.obj["hk"],
        scout_api=context.obj["scout"],
        beacon_api=context.obj["beacon"],
    )
    api.remove_vars(item_type=item_type, item_id=item_id)


@clean.command()
@click.option("-y", "--yes", is_flag=True, help="skip confirmation")
@click.option(
    "-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned"
)
@click.argument("case_id")
@click.argument("sample_info", type=click.File("r"))
@click.pass_context
def mip(context, yes, case_id, sample_info, dry_run: bool = False):
    """Remove analysis output."""

    raw_data = ruamel.yaml.safe_load(sample_info)
    date = context.obj["tb"].get_sampleinfo_date(raw_data)
    case_obj = context.obj["db"].family(case_id)

    if case_obj is None:
        LOG.error(f"{case_id}: family not found")
        context.abort()

    analysis_obj = context.obj["db"].analysis(case_obj, date)
    if analysis_obj is None:
        LOG.error(f"{case_id} - {date}: analysis not found")
        context.abort()

    try:
        context.obj["tb"].delete_analysis(case_id, date, yes=yes, dry_run=dry_run)
    except ValueError as error:
        LOG.error(f"{case_id}: {error.args[0]}")
        context.abort()


@clean.command()
@click.argument("bundle")
@click.option("-y", "--yes", is_flag=True, help="skip checks")
@click.option("-d", "--dry-run", is_flag=True, help="show files that would be cleaned")
@click.pass_context
def scout(context, bundle, yes, dry_run):
    files = []
    for tag in ["bam", "bai", "bam-index", "cram", "crai", "cram-index"]:
        files.extend(context.obj["hk"].get_files(bundle=bundle, tags=[tag]))
    for file_obj in files:
        if file_obj.is_included:
            question = f"{bundle}: remove file from file system and database: {file_obj.full_path}"
        else:
            question = f"{bundle}: remove file from database: {file_obj.full_path}"

        if yes or click.confirm(question):
            file_name = file_obj.full_path
            if file_obj.is_included and Path(file_name).exists():
                if not dry_run:
                    Path(file_name).unlink()

            if not dry_run:
                file_obj.delete()
                context.obj["hk"].commit()
                click.echo(f"{file_name} deleted")


@clean.command()
@click.option("-y", "--yes", is_flag=True, help="skip checks")
@click.option(
    "-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned"
)
@click.pass_context
def scoutauto(context, yes, dry_run):
    """Automatically clean up solved and archived scout cases"""
    bundles = []
    for status in "archived", "solved":
        cases = context.obj["scout"].get_cases(status=status, reruns=False)
        cases_added = 0
        for case in cases:
            x_days_ago = datetime.now() - case.get("analysis_date")
            if x_days_ago.days > 30:
                bundles.append(case.get("_id"))
                cases_added += 1
        LOG.info(f"{cases_added} cases marked for bam removal :)")

    for bundle in bundles:
        context.invoke(scout, bundle=bundle, yes=yes, dry_run=dry_run)


@clean.command()
@click.option("-y", "--yes", is_flag=True, help="skip confirmation")
@click.option(
    "-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned"
)
@click.argument("before_str")
@click.pass_context
def mipauto(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Automatically clean up "old" analyses."""
    before = parse_date(before_str)
    old_analyses = context.obj["db"].analyses(before=before)
    for status_analysis in old_analyses:
        case_id = status_analysis.family.internal_id
        LOG.debug(f"{case_id}: clean up analysis output")
        tb_analysis = context.obj["tb"].find_analysis(
            family=case_id, started_at=status_analysis.started_at, status="completed"
        )

        if tb_analysis is None:
            LOG.warning(f"{case_id}: analysis not found in Trailblazer")
            continue
        elif tb_analysis.is_deleted:
            LOG.warning(f"{case_id}: analysis already deleted")
            continue
        elif context.obj["tb"].analyses(family=case_id, temp=True).count() > 0:
            LOG.warning(f"{case_id}: family already re-started")
            continue

        try:
            sampleinfo_path = context.obj["tb"].get_sampleinfo(tb_analysis)
            LOG.info(f"{case_id}: cleaning MIP output")
            with open(sampleinfo_path, "r") as sampleinfo_file:
                context.invoke(
                    mip,
                    yes=yes,
                    case_id=case_id,
                    sample_info=sampleinfo_file,
                    dry_run=dry_run,
                )
        except FileNotFoundError:
            LOG.error(
                f"{case_id}: sample_info file not found, please mark the analysis as deleted in "
                f"the analysis table in trailblazer."
            )
