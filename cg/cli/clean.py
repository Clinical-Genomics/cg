"""cg module for cleaning databases and files"""
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import click

from cg.apps.scout.scout_export import ScoutExportCase
from cg.cli.workflow.commands import balsamic_past_run_dirs, mip_past_run_dirs
from cg.meta.meta import MetaAPI

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def clean(context):
    """Clean up processes"""
    return


clean.add_command(balsamic_past_run_dirs)
clean.add_command(mip_past_run_dirs)


@clean.command("hk-alignment-files")
@click.argument("bundle")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Show files that would be cleaned")
@click.pass_context
def hk_alignment_files(context, bundle, yes: bool = False, dry_run: bool = False):
    """Clean up alignment files in Housekeeper bundle"""

    meta_api = context.obj.get("meta_api") or MetaAPI(context.obj)
    context.obj["meta_api"] = meta_api

    if bundle is None:
        LOG.info("Please select a bundle")
        raise click.Abort
    files = []
    for tag in ["bam", "bai", "bam-index", "cram", "crai", "cram-index"]:
        files.extend(meta_api.housekeeper_api.get_files(bundle=bundle, tags=[tag]))
    for file_obj in files:
        if file_obj.is_included:
            question = f"{bundle}: remove file from file system and database: {file_obj.full_path}"
        else:
            question = f"{bundle}: remove file from database: {file_obj.full_path}"

        if yes or click.confirm(question):
            file_name = file_obj.full_path
            if file_obj.is_included and Path(file_name).exists() and not dry_run:
                Path(file_name).unlink()

            if not dry_run:
                file_obj.delete()
                meta_api.housekeeper_api.commit()
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

    meta_api = context.obj.get("meta_api") or MetaAPI(context.obj)
    context.obj["meta_api"] = meta_api

    bundles = []
    for status in ["archived", "solved"]:
        cases: List[ScoutExportCase] = meta_api.scout_api.get_cases(status=status, reruns=False)
        cases_added = 0
        for case in cases:
            x_days_ago = datetime.now() - case.analysis_date
            if x_days_ago.days > days_old:
                bundles.append(case.id)
                cases_added += 1
        LOG.info("%s cases marked for bam removal", cases_added)

    for bundle in bundles:
        context.invoke(hk_alignment_files, bundle=bundle, yes=yes, dry_run=dry_run)


@clean.command("hk-past-files")
@click.option("-c", "--case-id", type=str)
@click.option("-t", "--tags", multiple=True)
@click.option("-y", "--yes", is_flag=True, help="skip checks")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.pass_context
def hk_past_files(context, case_id: str, tags: list, yes: bool, dry_run: bool):
    """ Remove files found in older housekeeper bundles """

    meta_api = context.obj.get("meta_api") or MetaAPI(context.obj)
    context.obj["meta_api"] = meta_api

    if case_id:
        cases = [meta_api.status_db.family(case_id)]
    else:
        cases = meta_api.status_db.families()
    for case in cases:
        case_id = case.internal_id
        last_version = meta_api.housekeeper_api.last_version(bundle=case_id)
        if not last_version:
            continue
        last_version_file_paths = [
            Path(hk_file.full_path)
            for hk_file in meta_api.housekeeper_api.get_files(
                bundle=case_id, tags=None, version=last_version.id
            )
        ]
        LOG.info("Searching %s bundle for outdated files", case_id)
        hk_files = []
        for tag in tags:
            hk_files.extend(meta_api.housekeeper_api.get_files(bundle=case_id, tags=[tag]))
        for hk_file in hk_files:
            file_path = Path(hk_file.full_path)
            if file_path in last_version_file_paths:
                continue
            LOG.info("Will remove %s", file_path)
            if (yes or click.confirm("Do you want to remove this file?")) and not dry_run:
                hk_file.delete()
                meta_api.housekeeper_api.commit()
                if file_path.exists():
                    file_path.unlink()
                LOG.info("File removed")
