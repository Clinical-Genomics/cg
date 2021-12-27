"""cg module for cleaning databases and files"""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import click
from alchy import Query
from cgmodels.cg.constants import Pipeline
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
from cg.constants import FlowCellStatus, HousekeeperTags
from cg.meta.clean.demultiplexed_flow_cells import DemultiplexedRunsFlowCell
from cg.models.cg_config import CGConfig
from cg.store import Store

CHECK_COLOR = {True: "green", False: "red"}
LOG = logging.getLogger(__name__)
FLOW_CELL_OUTPUT_HEADERS = [
    "Flow cell run name",
    "Flow cell id",
    "Correct name?",
    "Exists in statusdb?",
    "Fastq files in HK?",
    "Spring files in HK?",
    "Files on disk?",
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


@clean.command("hk-bundle-files")
@click.option("-c", "--case_id", type=str, required=False)
@click.option("-p", "--pipeline", type=Pipeline, required=False)
@click.option("-t", "--tags", multiple=True, required=True)
@click.option("-o", "--days-old", type=int, default=30)
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.pass_obj
def hk_bundle_files(
    context: CGConfig,
    case_id: Optional[str],
    tags: list,
    days_old: Optional[int],
    pipeline: Optional[Pipeline],
    dry_run: bool,
):
    """Remove files found in housekeeper bundles"""

    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    status_db: Store = context.status_db

    date_threshold: datetime = datetime.now() - timedelta(days=days_old)

    analyses: Query = status_db.get_analyses_before_date(
        case_id=case_id, before=date_threshold, pipeline=pipeline
    )
    size_cleaned = 0
    for analysis in analyses:
        LOG.info(f"Cleaning analysis {analysis}")
        bundle_name: str = analysis.family.internal_id
        hk_bundle_version: Optional[hk_models.Version] = housekeeper_api.version(
            bundle=bundle_name, date=analysis.started_at
        )
        if not hk_bundle_version:
            LOG.warning(
                f"Version not found for "
                f"bundle:{bundle_name}; "
                f"pipeline: {analysis.pipeline}; "
                f"date {analysis.started_at}"
            )
            continue

        LOG.info(
            f"Version found for "
            f"bundle:{bundle_name}; "
            f"pipeline: {analysis.pipeline}; "
            f"date {analysis.started_at}"
        )
        version_files: List[hk_models.File] = housekeeper_api.get_files(
            bundle=analysis.family.internal_id, tags=tags, version=hk_bundle_version.id
        ).all()
        for version_file in version_files:
            file_path: Path = Path(version_file.full_path)
            if not file_path.exists():
                LOG.info(f"File {file_path} not on disk.")
                continue
            LOG.info(f"File {file_path} found on disk.")
            file_size = file_path.stat().st_size
            size_cleaned += file_size
            if dry_run:
                continue

            file_path.unlink()
            housekeeper_api.delete_file(version_file.id)
            housekeeper_api.commit()
            LOG.info(f"Removed file {file_path}. Dry run: {dry_run}")

    LOG.info(f"Process freed {round(size_cleaned * 0.0000000001, 2)}GB. Dry run: {dry_run}")


@clean.command("invalid-flow-cell-dirs")
@click.option("-f", "--failed-only", is_flag=True, help="Shows failed flow cells only")
@click.option(
    "-d",
    "--dry-run",
    is_flag=True,
    help="Runs this command without actually removing flow cells!",
)
@click.pass_obj
def remove_invalid_flow_cell_directories(context: CGConfig, failed_only: bool, dry_run: bool):
    """Removes invalid flow cell directories from demultiplexed-runs"""
    status_db: Store = context.status_db
    demux_api: DemultiplexingAPI = context.demultiplex_api
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    checked_flow_cells: List[DemultiplexedRunsFlowCell] = []
    fastq_files_in_housekeeper: Query = housekeeper_api.files(tags=[HousekeeperTags.FASTQ])
    spring_files_in_housekeeper: Query = housekeeper_api.files(tags=[HousekeeperTags.SPRING])
    for flow_cell_dir in demux_api.out_dir.iterdir():
        flow_cell_obj: DemultiplexedRunsFlowCell = DemultiplexedRunsFlowCell(
            flow_cell_dir,
            status_db,
            housekeeper_api,
            fastq_files_in_housekeeper,
            spring_files_in_housekeeper,
        )
        checked_flow_cells.append(flow_cell_obj)

    failed_flow_cells: List[DemultiplexedRunsFlowCell] = [
        flow_cell for flow_cell in checked_flow_cells if not flow_cell.passed_check
    ]
    flow_cells_to_present: List[DemultiplexedRunsFlowCell] = (
        failed_flow_cells if failed_only else checked_flow_cells
    )
    tabulate_row = [
        [
            flow_cell.run_name,
            flow_cell.id,
            flow_cell.is_correctly_named,
            flow_cell.exists_in_statusdb,
            flow_cell.fastq_files_exist_in_housekeeper,
            flow_cell.spring_files_exist_in_housekeeper,
            flow_cell.files_exist_in_housekeeper,
            click.style(str(flow_cell.passed_check), fg=CHECK_COLOR[flow_cell.passed_check]),
        ]
        for flow_cell in flow_cells_to_present
    ]

    click.echo(
        tabulate(
            tabulate_row,
            headers=FLOW_CELL_OUTPUT_HEADERS,
            tablefmt="fancy_grid",
            missingval="N/A",
        ),
    )

    for flow_cell in failed_flow_cells:
        LOG.warning("Invalid flow cell directory found: %s", flow_cell.path)
        if dry_run:
            continue
        LOG.warning("Removing %s!", flow_cell.path)
        flow_cell.remove_failed_flow_cell()


@clean.command("fix-flow-cell-status")
@click.option(
    "-d",
    "--dry-run",
    is_flag=True,
    help="Runs this command without actually fixing flow cell statuses!",
)
@click.pass_obj
def fix_flow_cell_status(context: CGConfig, dry_run: bool):
    """set correct flow cell statuses in statusdb"""
    status_db: Store = context.status_db
    demux_api: DemultiplexingAPI = context.demultiplex_api
    housekeeper_api: HousekeeperAPI = context.housekeeper_api

    flow_cells_in_statusdb = [
        flow_cell
        for flow_cell in status_db.flowcells()
        if flow_cell.status in [FlowCellStatus.ONDISK, FlowCellStatus.REMOVED]
    ]
    LOG.info(
        "Number of flow cells with status 'ondisk' or 'removed' in statusdb: %s",
        len(flow_cells_in_statusdb),
    )
    physical_ondisk_flow_cell_names = [
        DemultiplexedRunsFlowCell(
            flow_cell_dir,
            status_db,
            housekeeper_api,
        ).id
        for flow_cell_dir in demux_api.out_dir.iterdir()
    ]
    for flow_cell in flow_cells_in_statusdb:
        status_db_flow_cell_status = flow_cell.status
        new_status = (
            FlowCellStatus.ONDISK
            if flow_cell.run_name in physical_ondisk_flow_cell_names
            else FlowCellStatus.REMOVED
        )
        if status_db_flow_cell_status != new_status:
            LOG.info(
                "Setting status of flow cell %s from %s to %s",
                flow_cell.run_name,
                status_db_flow_cell_status,
                new_status,
            )
            if dry_run:
                continue
            flow_cell.status = new_status
            status_db.commit()
