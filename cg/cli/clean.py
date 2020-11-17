"""cg module for cleaning databases and files"""
import logging
import shutil
from datetime import datetime
from pathlib import Path

import click
from dateutil.parser import parse as parse_date

from cg.apps.balsamic.api import BalsamicAPI
from cg.apps.balsamic.fastq import FastqHandler
from cg.apps.crunchy import CrunchyAPI
from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.store import Store


LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def clean(context):
    """Clean up processes"""
    context.obj["status_db"] = Store(context.obj["database"])
    context.obj["housekeeper_api"] = HousekeeperAPI(context.obj)
    context.obj["trailblazer_api"] = TrailblazerAPI(context.obj)
    context.obj["scout_api"] = ScoutAPI(context.obj)
    context.obj["crunchy_api"] = CrunchyAPI(context.obj)
    context.obj["lims_api"] = LimsAPI(context.obj)

    context.obj["BalsamicAnalysisAPI"] = BalsamicAnalysisAPI(
        balsamic_api=BalsamicAPI(context.obj),
        store=context.obj["status_db"],
        housekeeper_api=context.obj["housekeeper_api"],
        fastq_handler=FastqHandler(context.obj),
        lims_api=context.obj["lims_api"],
        trailblazer_api=context.obj["trailblazer_api"],
    )
    context.obj["MipAnalysisAPI"] = MipAnalysisAPI(
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

    if dry_run:
        LOG.info("Would have deleted: %s", analysis_path)
        return EXIT_SUCCESS

    if yes or click.confirm(f"Are you sure you want to remove all files in {analysis_path}?"):
        if not analysis_path.exists():
            LOG.warning("could not find: %s", analysis_path)
            return EXIT_FAIL
        if analysis_path.is_symlink():
            LOG.warning(
                "Will not automatically delete symlink: %s, delete it manually", analysis_path
            )
            return EXIT_FAIL

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
@click.pass_context
def mip_run_dir(context, yes, case_id, dry_run: bool = False):
    """Remove MIP run directory"""

    mip_analysis_api = context.obj["MipAnalysisAPI"]
    case_obj = mip_analysis_api.get_case_object(case_id)

    if case_obj is None:
        LOG.error("%s: family not found", case_id)
        raise click.Abort()

    analysis_path = mip_analysis_api.get_case_output_path(case_id=case_id)
    if not analysis_path.exists():
        LOG.error(f"No analysis directory found for {case_id}")
        raise click.Abort()

    if dry_run:
        LOG.info(f"Cleaning case {case_id} : Would have deleted contents of {analysis_path}")
        return

    try:
        if mip_analysis_api.is_latest_analysis_ongoing(case_id):
            LOG.warning(f"Analysis for case {case_id} is still ongoing!")

        if yes or click.confirm(f"Are you sure you want to remove {case_id}?"):
            shutil.rmtree(analysis_path, ignore_errors=True)
            LOG.info(f"Cleaning case {case_id} : Deleted contents of {analysis_path}")
            mip_analysis_api.mark_analyses_deleted(case_id)
            for analysis_obj in case_obj.analyses:
                analysis_obj.cleaned_at = analysis_obj.cleaned_at or datetime.now()
            mip_analysis_api.db.commit()
    except Exception as error:
        LOG.error(f"{case_id}: {error}")
        raise click.Abort()


@clean.command("hk-alignment-files")
@click.argument("bundle")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Show files that would be cleaned")
@click.pass_context
def hk_alignment_files(context, bundle, yes: bool = False, dry_run: bool = False):
    """Clean up alignment files in Housekeeper bundle"""
    files = []
    for tag in ["bam", "bai", "bam-index", "cram", "crai", "cram-index"]:
        files.extend(context.obj["housekeeper_api"].get_files(bundle=bundle, tags=[tag]))
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
                context.obj["housekeeper_api"].commit()
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
        LOG.info(f"{cases_added} cases marked for bam removal")

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
        cases = [context.obj["status_db"].family(case_id)]
    else:
        cases = context.obj["status_db"].families()
    for case in cases:
        case_id = case.internal_id
        last_version = context.obj["housekeeper_api"].last_version(bundle=case_id)
        if not last_version:
            continue
        last_version_file_paths = [
            Path(hk_file.full_path)
            for hk_file in context.obj["housekeeper_api"].get_files(
                bundle=case_id, tags=None, version=last_version.id
            )
        ]
        LOG.info("Searching %s bundle for outdated files", case_id)
        hk_files = []
        for tag in tags:
            hk_files.extend(context.obj["housekeeper_api"].get_files(bundle=case_id, tags=[tag]))
        for hk_file in hk_files:
            file_path = Path(hk_file.full_path)
            if file_path in last_version_file_paths:
                continue
            LOG.info("Will remove %s", file_path)
            if yes or click.confirm("Do you want to remove this file?"):
                if not dry_run:
                    hk_file.delete()
                    context.obj["housekeeper_api"].commit()
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
    mip_analysis_api = context.obj["MipAnalysisAPI"]
    before = parse_date(before_str)
    old_analyses = mip_analysis_api.get_analyses_to_clean(before=before)
    for status_analysis in old_analyses:
        case_id = status_analysis.family.internal_id
        try:
            context.invoke(
                mip_run_dir,
                yes=yes,
                case_id=case_id,
                dry_run=dry_run,
            )
        except click.Abort:
            continue
