"""cg module for cleaning databases and files"""
import logging

import ruamel.yaml
import click
from dateutil.parser import parse as parse_date
from datetime import datetime
from pathlib import Path

from cg.apps import crunchy, tb, hk, scoutapi, beacon as beacon_app
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
    context.obj["crunchy"] = crunchy.CrunchyAPI(context.obj)


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
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.argument("case_id")
@click.argument("sample_info", type=click.File("r"))
@click.pass_context
def mip(context, yes, case_id, sample_info, dry_run: bool = False):
    """Remove analysis output."""

    raw_data = ruamel.yaml.safe_load(sample_info)
    date = context.obj["tb"].get_sampleinfo_date(raw_data)
    case_obj = context.obj["db"].family(case_id)

    if case_obj is None:
        LOG.error("%s: family not found", case_id)
        context.abort()

    analysis_obj = context.obj["db"].analysis(case_obj, date)
    if analysis_obj is None:
        LOG.error("%s - %s: analysis not found", case_id, date)
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
def scout(context, bundle, yes: bool = False, dry_run: bool = False):
    """Clean alignment related files for a bundle in Housekeeper"""
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
@click.option(
    "--days-old",
    type=int,
    default=300,
    help="Clean alignment files with analysis dates oldar then given number of days",
)
@click.option("-y", "--yes", is_flag=True, help="skip checks")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.pass_context
def scoutauto(context, days_old: int, yes: bool = False, dry_run: bool = False):
    """Automatically clean up solved and archived scout cases"""
    bundles = []
    for status in "archived", "solved":
        cases = context.obj["scout"].get_cases(status=status, reruns=False)
        cases_added = 0
        for case in cases:
            x_days_ago = datetime.now() - case.get("analysis_date")
            if x_days_ago.days > days_old:
                bundles.append(case.get("_id"))
                cases_added += 1
        LOG.info("%s cases marked for bam removal :)", cases_added)

    for bundle in bundles:
        context.invoke(scout, bundle=bundle, yes=yes, dry_run=dry_run)


@clean.command("hk-past-files")
@click.option("-c", "--case-id", type=str)
@click.option("-t", "--tags", multiple=True)
@click.option("-y", "--yes", is_flag=True, help="skip checks")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.pass_context
def hk_past_files(context, case_id, tags, yes, dry_run):
    """ Remove files found in older housekeeper bundles """
    if case_id:
        cases = [context.obj["db"].family(case_id)]
    else:
        cases = context.obj["db"].families()
    for case in cases:
        case_id = case.internal_id
        bundle = context.obj["hk"].bundle(case_id)
        if not bundle:
            continue
        last_version = context.obj["hk"].last_version(bundle=case_id)
        if not last_version:
            continue
        last_version_file_paths = [
            Path(hk_file.full_path)
            for hk_file in context.obj["hk"].get_files(
                bundle=case_id, tags=None, version=last_version.id
            )
        ]
        LOG.info("Searching %s bundle for outdated files", case_id)
        hk_files = []
        for tag in tags:
            hk_files.extend(context.obj["hk"].get_files(bundle=case_id, tags=[tag]))
        for hk_file in hk_files:
            file_path = Path(hk_file.full_path)
            if file_path in last_version_file_paths:
                continue
            LOG.info("Will remove %s", file_path)
            if yes or click.confirm("Do you want to remove this file?"):
                if not dry_run:
                    hk_file.delete()
                    context.obj["hk"].commit()
                    if file_path.exists():
                        file_path.unlink()
                    LOG.info("File removed")


@clean.command()
@click.option("-y", "--yes", is_flag=True, help="skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.argument("before_str")
@click.pass_context
def mipauto(context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False):
    """Automatically clean up "old" analyses."""
    before = parse_date(before_str)
    old_analyses = context.obj["db"].analyses(before=before)
    for status_analysis in old_analyses:
        case_id = status_analysis.family.internal_id
        LOG.debug("%s: clean up analysis output", case_id)
        tb_analysis = context.obj["tb"].find_analysis(
            family=case_id, started_at=status_analysis.started_at, status="completed"
        )

        if tb_analysis is None:
            LOG.warning("%s: analysis not found in Trailblazer", case_id)
            continue
        elif tb_analysis.is_deleted:
            LOG.warning("%s: analysis already deleted", case_id)
            continue
        elif context.obj["tb"].analyses(family=case_id, temp=True).count() > 0:
            LOG.warning("%s: family already re-started", case_id)
            continue

        try:
            sampleinfo_path = context.obj["tb"].get_sampleinfo(tb_analysis)
            LOG.info("%s: cleaning MIP output", case_id)
            with open(sampleinfo_path, "r") as sampleinfo_file:
                context.invoke(
                    mip, yes=yes, case_id=case_id, sample_info=sampleinfo_file, dry_run=dry_run
                )
        except FileNotFoundError:
            LOG.error(
                (
                    "%s: sample_info file not found, please mark the analysis as deleted in the "
                    "analysis table in trailblazer."
                ),
                case_id,
            )
