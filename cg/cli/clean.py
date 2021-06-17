"""cg module for cleaning databases and files"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import click
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.scout.scout_export import ScoutExportCase
from cg.apps.scout.scoutapi import ScoutAPI
from cg.cli.workflow.commands import (
    balsamic_past_run_dirs,
    rsync_past_run_dirs,
    mip_past_run_dirs,
    mutant_past_run_dirs,
    fluffy_past_run_dirs,
)
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)


@click.group()
def clean():
    """Clean up processes"""
    return


clean.add_command(balsamic_past_run_dirs)
clean.add_command(fluffy_past_run_dirs)
clean.add_command(mip_past_run_dirs)
clean.add_command(mutant_past_run_dirs)
clean.add_command(rsync_past_run_dirs)


@clean.command("hk-alignment-files")
@click.argument("bundle")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Show files that would be cleaned")
@click.pass_obj
def hk_alignment_files(context: CGConfig, bundle: str, yes: bool = False, dry_run: bool = False):
    """Clean up alignment files in Housekeeper bundle"""
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    for tag in ["bam", "bai", "bam-index", "cram", "crai", "cram-index"]:

        tag_files = set(housekeeper_api.get_files(bundle=bundle, tags=[tag]))

        if not tag_files:
            LOG.warning(
                "Could not find any files ready for cleaning for bundle %s and tag %s", bundle, tag
            )

        for file_obj in tag_files:
            if not (yes or click.confirm(_get_confirm_question(bundle, file_obj))):
                continue

            file_path: Path = Path(file_obj.full_path)
            if file_obj.is_included and file_path.exists():
                LOG.info("Unlinking %s", file_path)
                if not dry_run:
                    file_path.unlink()

            LOG.info("Deleting %s from database", file_path)
            if not dry_run:
                file_obj.delete()
                housekeeper_api.commit()


def _get_confirm_question(bundle, file_obj):
    if file_obj.is_included:
        question = f"{bundle}: remove file from file system and database: {file_obj.full_path}"
    else:
        question = f"{bundle}: remove file from database: {file_obj.full_path}"
    return question


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
def scout_finished_cases(
    context: click.Context, days_old: int, yes: bool = False, dry_run: bool = False
):
    """Clean up of solved and archived scout cases"""
    scout_api: ScoutAPI = context.obj.scout_api
    bundles: List[str] = []
    for status in ["archived", "solved"]:
        cases: List[ScoutExportCase] = scout_api.get_cases(status=status, reruns=False)
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
@click.pass_obj
def hk_past_files(context: CGConfig, case_id: str, tags: list, yes: bool, dry_run: bool):
    """Remove files found in older housekeeper bundles"""

    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    status_db: Store = context.status_db

    cases: Iterable[models.Family]
    if case_id:
        cases: List[models.Family] = [status_db.family(case_id)]
    else:
        cases: Iterable[models.Family] = status_db.families()
    for case in cases:
        case_id = case.internal_id
        last_version: Optional[hk_models.Version] = housekeeper_api.last_version(bundle=case_id)
        if not last_version:
            continue
        last_version_file_paths: List[Path] = [
            Path(hk_file.full_path)
            for hk_file in housekeeper_api.get_files(
                bundle=case_id, tags=None, version=last_version.id
            )
        ]
        LOG.info("Searching %s bundle for outdated files", case_id)
        hk_files: List[hk_models.File] = []
        for tag in tags:
            hk_files.extend(housekeeper_api.get_files(bundle=case_id, tags=[tag]))
        for hk_file in hk_files:
            file_path = Path(hk_file.full_path)
            if file_path in last_version_file_paths:
                continue
            LOG.info("Will remove %s", file_path)
            if (yes or click.confirm("Do you want to remove this file?")) and not dry_run:
                hk_file.delete()
                housekeeper_api.commit()
                if file_path.exists():
                    file_path.unlink()
                LOG.info("File removed")
