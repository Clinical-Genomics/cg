"""cg module for cleaning databases and files"""
import logging
from datetime import datetime
from pathlib import Path
import shutil
import ruamel.yaml
import click
from dateutil.parser import parse as parse_date

from cg.apps.balsamic.fastq import FastqHandler
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.scoutapi import ScoutAPI
from cg.apps.crunchy import CrunchyAPI
from cg.apps.balsamic.api import BalsamicAPI
from cg.store import Store
from cg.constants import EXIT_SUCCESS, EXIT_FAIL

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def clean(context):
    """Clean up processes"""
    context.obj["store_api"] = Store(context.obj["database"])
    context.obj["hk_api"] = HousekeeperAPI(context.obj)
    context.obj["tb_api"] = TrailblazerAPI(context.obj)
    context.obj["scout_api"] = ScoutAPI(context.obj)
    context.obj["crunchy_api"] = CrunchyAPI(context.obj)
    context.obj["BalsamicAnalysisAPI"] = BalsamicAnalysisAPI(
        balsamic_api=BalsamicAPI(context.obj),
        store=context.obj["store_api"],
        housekeeper_api=context.obj["hk_api"],
        fastq_handler=FastqHandler(context.obj),
        lims_api=LimsAPI(context.obj),
    )


@clean.command("balsamic-run-dir")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.argument("case_id")
@click.pass_context
def balsamic_run_dir(context, yes, case_id, dry_run: bool = False):
    """Remove Balsamic run directory"""

    balsamic_analysis_api = context.obj["BalsamicAnalysisAPI"]
    case_object = balsamic_analysis_api.get_case_object(case_id)
    if not case_object:
        LOG.warning(f"{case_id} not found!")
        raise click.Abort()

    analysis_obj = case_object.analyses[0] if case_object.analyses else None
    if not analysis_obj:
        LOG.error("%s: analysis not found", case_id)
        raise click.Abort()

    analysis_path = Path(balsamic_analysis_api.get_case_path(case_id))
    if yes or click.confirm(f"Do you want to remove {analysis_path}?"):
        if not analysis_path.exists():
            LOG.warning("could not find: %s", analysis_path)
            return EXIT_FAIL
        if analysis_path.is_symlink():
            LOG.warning(
                "Will not automatically delete symlink: %s, delete it manually", analysis_path
            )
            return EXIT_FAIL
        if dry_run:
            LOG.info("Would have deleted: %s", analysis_path)
            return EXIT_SUCCESS
        try:
            shutil.rmtree(analysis_path, ignore_errors=True)
            LOG.info(f"Cleaned {analysis_path}")
        except Exception as e:
            LOG.warning(
                f" Directory {analysis_path} will not be deleted due to unexpected error - {e}!"
            )

        analysis_obj.cleaned_at = datetime.now()
        balsamic_analysis_api.store.commit()


@clean.command("mip-run-dir")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.argument("case_id")
@click.argument("sample_info", type=click.File("r"))
@click.pass_context
def mip_run_dir(context, yes, case_id, sample_info, dry_run: bool = False):
    """Remove MIP run directory"""

    raw_data = ruamel.yaml.safe_load(sample_info)
    date = context.obj["tb_api"].get_sampleinfo_date(raw_data)
    case_obj = context.obj["store_api"].family(case_id)

    if case_obj is None:
        LOG.error("%s: family not found", case_id)
        context.abort()

    analysis_obj = context.obj["store_api"].analysis(case_obj, date)
    if analysis_obj is None:
        LOG.error("%s - %s: analysis not found", case_id, date)
        context.abort()

    try:
        context.obj["tb_api"].delete_analysis(case_id, date, yes=yes, dry_run=dry_run)
        analysis_obj.cleaned_at = datetime.now()
    except ValueError as error:
        LOG.error(f"{case_id}: {error.args[0]}")
        context.abort()


@clean.command("hk-alignment-files")
@click.argument("bundle")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Show files that would be cleaned")
@click.pass_context
def hk_alignment_files(context, bundle, yes: bool = False, dry_run: bool = False):
    """Clean up alignment files in Housekeeper bundle"""
    files = []
    for tag in ["bam", "bai", "bam-index", "cram", "crai", "cram-index"]:
        files.extend(context.obj["hk_api"].get_files(bundle=bundle, tags=[tag]))
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
                context.obj["hk_api"].commit()
                click.echo(f"{file_name} deleted")


@clean.command("scout-finished-cases")
@click.option(
    "--days-old",
    type=int,
    default=300,
    help="Clean alignment files with analysis dates older then given number of days",
)
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.pass_context
def scout_finished_cases(context, days_old: int, yes: bool = False, dry_run: bool = False):
    """Clean up of solved and archived scout cases"""
    bundles = []
    for status in "archived", "solved":
        cases = context.obj["scout_api"].get_cases(status=status, reruns=False)
        cases_added = 0
        for case in cases:
            x_days_ago = datetime.now() - case.get("analysis_date")
            if x_days_ago.days > days_old:
                bundles.append(case.get("_id"))
                cases_added += 1
        LOG.info("%s cases marked for bam removal :)", cases_added)

    for bundle in bundles:
        context.invoke(hk_alignment_files, bundle=bundle, yes=yes, dry_run=dry_run)


@clean.command("hk-past-files")
@click.option("-c", "--case-id", type=str)
@click.option("-t", "--tags", multiple=True)
@click.option("-y", "--yes", is_flag=True, help="skip checks")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.pass_context
def hk_past_files(context, case_id, tags, yes, dry_run):
    """ Remove files found in older housekeeper bundles """
    if case_id:
        cases = [context.obj["store_api"].family(case_id)]
    else:
        cases = context.obj["store_api"].families()
    for case in cases:
        case_id = case.internal_id
        last_version = context.obj["hk_api"].last_version(bundle=case_id)
        if not last_version:
            continue
        last_version_file_paths = [
            Path(hk_file.full_path)
            for hk_file in context.obj["hk_api"].get_files(
                bundle=case_id, tags=None, version=last_version.id
            )
        ]
        LOG.info("Searching %s bundle for outdated files", case_id)
        hk_files = []
        for tag in tags:
            hk_files.extend(context.obj["hk_api"].get_files(bundle=case_id, tags=[tag]))
        for hk_file in hk_files:
            file_path = Path(hk_file.full_path)
            if file_path in last_version_file_paths:
                continue
            LOG.info("Will remove %s", file_path)
            if yes or click.confirm("Do you want to remove this file?"):
                if not dry_run:
                    hk_file.delete()
                    context.obj["hk_api"].commit()
                    if file_path.exists():
                        file_path.unlink()
                    LOG.info("File removed")


@clean.command("balsamic-past-run-dirs")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.argument("before_str")
@click.pass_context
def balsamic_past_run_dirs(context, before_str: str, yes: bool = False, dry_run: bool = False):
    """Clean up of "old" Balsamic case run dirs"""

    before = parse_date(before_str)
    balsamic_analysis_api = context.obj["BalsamicAnalysisAPI"]
    possible_cleanups = balsamic_analysis_api.get_analyses_to_clean(before_date=before)
    LOG.info(f"Cleaning all analyses created before {before}")

    # for all analyses
    for analysis in possible_cleanups:
        case_id = analysis.family.internal_id

        # call clean
        LOG.info(f"Cleaning Balsamic output for {case_id}")
        try:
            context.invoke(balsamic_run_dir, yes=yes, case_id=case_id, dry_run=dry_run)
        except click.Abort:
            continue

    LOG.info("Done cleaning Balsamic output")


@clean.command("mip-past-run-dirs")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.argument("before_str")
@click.pass_context
def mip_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" MIP case run dirs"""
    before = parse_date(before_str)
    old_analyses = context.obj["store_api"].analyses(before=before)
    for status_analysis in old_analyses:
        case_id = status_analysis.family.internal_id
        LOG.debug("%s: clean up analysis output", case_id)
        tb_analysis = context.obj["tb_api"].find_analysis(
            family=case_id, started_at=status_analysis.started_at, status="completed"
        )

        if tb_analysis is None:
            LOG.warning("%s: analysis not found in Trailblazer", case_id)
            continue
        elif tb_analysis.is_deleted:
            LOG.warning("%s: analysis already deleted", case_id)
            continue
        elif context.obj["tb_api"].analyses(family=case_id, temp=True).count() > 0:
            LOG.warning("%s: family already re-started", case_id)
            continue

        try:
            sampleinfo_path = context.obj["tb_api"].get_sampleinfo(tb_analysis)
            LOG.info("%s: cleaning MIP output", case_id)
            with open(sampleinfo_path, "r") as sampleinfo_file:
                context.invoke(
                    mip_run_dir,
                    yes=yes,
                    case_id=case_id,
                    sample_info=sampleinfo_file,
                    dry_run=dry_run,
                )
        except FileNotFoundError:
            LOG.error(
                (
                    "%s: sample_info file not found, please mark the analysis as deleted in the "
                    "analysis table in trailblazer."
                ),
                case_id,
            )
