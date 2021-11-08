"""cg module for cleaning databases and files"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import click
from housekeeper.store import models as hk_models
from tabulate import tabulate

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.scout.scout_export import ScoutExportCase
from cg.apps.scout.scoutapi import ScoutAPI
from cg.cli.workflow.commands import (
    balsamic_past_run_dirs,
    fluffy_past_run_dirs,
    mip_past_run_dirs,
    mutant_past_run_dirs,
    rsync_past_run_dirs,
)
from cg.meta.clean.demultiplexed_flowcells import DemuxedFlowcell
from cg.models.cg_config import CGConfig
from cg.store import Store, models

CHECK_COLOR = {True: "green", False: "red"}
LOG = logging.getLogger(__name__)
FLOWCELL_OUTPUT_HEADERS = [
    "Flowcell name",
    "Flowcell id",
    "Correct name?",
    "Exists in statusdb?",
    "Status",
    "Fastq files in HK?",
    # "Fastq files on disk?",
    "Check passed?",
]


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


@clean.command("demux-runs-flowcells")
@click.option("-f", "--failed-only", is_flag=True, help="Shows failed flowcells only")
@click.option(
    "-r",
    "--remove-failed",
    is_flag=True,
    help="CAUTION: REMOVES FLOWCELL DIRS FROM DEMULTIPLEXED-RUNS!",
)
@click.option(
    "-d",
    "--dry-run",
    is_flag=True,
    help="Runs this command without actually removing " "flowcells!",
)
@click.pass_obj
def demux_runs_flowcells(context: CGConfig, failed_only: bool, remove_failed: bool, dry_run: bool):
    status_db: Store = context.status_db
    demux_api: DemultiplexingAPI = context.demultiplex_api
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    checked_flowcells = []
    for flowcell_dir in demux_api.out_dir.iterdir():
        flowcell_obj = DemuxedFlowcell(flowcell_dir, status_db, housekeeper_api)
        flowcell_obj.check_existing_flowcell_directory()
        checked_flowcells.append(flowcell_obj)
    failed_flowcells = [flowcell for flowcell in checked_flowcells if not flowcell.passed_check]
    if failed_only:
        tabulate_row = [
            [
                flowcell.flowcell_name,
                flowcell.flowcell_id,
                flowcell.is_correctly_named,
                flowcell.flowcell_exists_in_status_db,
                flowcell.flowcell_status,
                flowcell.fastq_files_exist_in_housekeeper,
                # flowcell.fastq_files_exist_on_disk,
                click.style(str(flowcell.passed_check), fg="red"),
            ]
            for flowcell in failed_flowcells
        ]
    else:
        tabulate_row = [
            [
                flowcell.flowcell_name,
                flowcell.flowcell_id,
                flowcell.is_correctly_named,
                flowcell.flowcell_exists_in_status_db,
                flowcell.flowcell_status,
                flowcell.fastq_files_exist_in_housekeeper,
                # flowcell.fastq_files_exist_on_disk,
                click.style(str(flowcell.passed_check), fg=CHECK_COLOR[flowcell.passed_check]),
            ]
            for flowcell in checked_flowcells
        ]

    click.echo(
        tabulate(
            tabulate_row,
            headers=FLOWCELL_OUTPUT_HEADERS,
            tablefmt="fancy_grid",
            missingval="?",
        ),
    )
    if remove_failed:
        for flowcell in failed_flowcells:
            LOG.warning("Removing %s from 'demultiplexed-runs'!", flowcell.flowcell_path)
            if not dry_run:
                flowcell.remove_from_demultiplexed_runs()


@clean.command("statusdb-flowcells")
@click.option("-f", "--failed-only", is_flag=True, help="Shows failed flowcells only")
@click.option(
    "-r",
    "--remove-failed",
    is_flag=True,
    help="CAUTION: REMOVES FLOWCELL DIRS FROM DEMULTIPLEXED-RUNS!",
)
@click.option(
    "-d",
    "--dry-run",
    is_flag=True,
    help="Runs this command without actually removing " "flowcells!",
)
@click.pass_obj
def statusdb_flowcells(context: CGConfig, failed_only: bool, remove_failed: bool, dry_run: bool):
    """check flowcell statuses in statusdb"""
    status_db: Store = context.status_db
    ondisk_flowcells = status_db.flowcells(status="ondisk")
    click.echo(f"Found {ondisk_flowcells.count()} on disk flowcells!")
