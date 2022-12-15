"""cg module for cleaning databases and files."""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import click
from alchy import Query
from cgmodels.cg.constants import Pipeline
from tabulate import tabulate

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.scout.scout_export import ScoutExportCase
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.cli.workflow.commands import (
    balsamic_past_run_dirs,
    fluffy_past_run_dirs,
    mip_past_run_dirs,
    mutant_past_run_dirs,
    rnafusion_past_run_dirs,
    rsync_past_run_dirs,
    microsalt_past_run_dirs,
)
from cg.constants import FlowCellStatus
from cg.constants.constants import DRY_RUN
from cg.constants.sequencing import Sequencers
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.meta.clean.api import CleanAPI
from cg.meta.clean.demultiplexed_flow_cells import DemultiplexedRunsFlowCell
from cg.meta.clean.flow_cell_run_directories import RunDirFlowCell
from cg.models.cg_config import CGConfig
from cg.store import Store
from housekeeper.store import models as hk_models

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
clean.add_command(rnafusion_past_run_dirs)
clean.add_command(rsync_past_run_dirs)
clean.add_command(microsalt_past_run_dirs)


def get_date_days_ago(days_ago: int) -> datetime:
    """Calculate the date 'days_ago'"""
    return datetime.now() - timedelta(days=days_ago)


@clean.command("hk-alignment-files")
@click.argument("bundle")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@DRY_RUN
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


def _get_confirm_question(bundle, file_obj) -> str:
    """Return confirmation question."""
    return (
        f"{bundle}: remove file from file system and database: {file_obj.full_path}"
        if file_obj.is_included
        else f"{bundle}: remove file from database: {file_obj.full_path}"
    )


@clean.command("scout-finished-cases")
@click.option(
    "--days-old",
    type=int,
    default=300,
    help="Clean alignment files with analysis dates older then given number of days",
)
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@DRY_RUN
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


@clean.command("hk-case-bundle-files")
@click.option(
    "--days-old",
    type=int,
    default=365,
    help="Clean all files with analysis dates older then given number of days",
)
@DRY_RUN
@click.pass_context
def hk_case_bundle_files(context: CGConfig, days_old: int, dry_run: bool = False):
    """Clean up all non-protected files for all pipelines"""
    housekeeper_api: HousekeeperAPI = context.obj.housekeeper_api
    clean_api: CleanAPI = CleanAPI(status_db=context.obj.status_db, housekeeper_api=housekeeper_api)

    size_cleaned: int = 0
    version_file: hk_models.File
    for version_file in clean_api.get_unprotected_existing_bundle_files(
        before=get_date_days_ago(days_ago=days_old)
    ):
        file_path: Path = Path(version_file.full_path)
        file_size: int = file_path.stat().st_size
        size_cleaned += file_size
        if dry_run:
            LOG.info("Dry run: %s. Keeping file %s", dry_run, file_path)
            continue

        file_path.unlink()
        housekeeper_api.delete_file(version_file.id)
        housekeeper_api.commit()
        LOG.info("Removed file %s. Dry run: %s", file_path, dry_run)

    LOG.info("Process freed %s GB. Dry run: %s", round(size_cleaned * 0.0000000001, 2), dry_run)


@clean.command("hk-bundle-files")
@click.option("-c", "--case_id", type=str, required=False)
@click.option("-p", "--pipeline", type=Pipeline, required=False)
@click.option("-t", "--tags", multiple=True, required=True)
@click.option("-o", "--days-old", type=int, default=30)
@DRY_RUN
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

    date_threshold: datetime = get_date_days_ago(days_ago=days_old)

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
@DRY_RUN
@click.pass_obj
def remove_invalid_flow_cell_directories(context: CGConfig, failed_only: bool, dry_run: bool):
    """Removes invalid flow cell directories from demultiplexed-runs"""
    status_db: Store = context.status_db
    demux_api: DemultiplexingAPI = context.demultiplex_api
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    trailblazer_api: TrailblazerAPI = context.trailblazer_api
    sample_sheets_dir: str = context.clean.flow_cells.sample_sheets_dir_name
    checked_flow_cells: List[DemultiplexedRunsFlowCell] = []
    search = f"%{demux_api.out_dir}%"
    fastq_files_in_housekeeper: Query = housekeeper_api.files(
        tags=[SequencingFileTag.FASTQ]
    ).filter(hk_models.File.path.like(search))
    spring_files_in_housekeeper: Query = housekeeper_api.files(
        tags=[SequencingFileTag.SPRING]
    ).filter(hk_models.File.path.like(search))
    for flow_cell_dir in demux_api.out_dir.iterdir():
        flow_cell_obj: DemultiplexedRunsFlowCell = DemultiplexedRunsFlowCell(
            flow_cell_dir,
            status_db,
            housekeeper_api,
            trailblazer_api,
            sample_sheets_dir,
            fastq_files_in_housekeeper,
            spring_files_in_housekeeper,
        )
        if not flow_cell_obj.is_demultiplexing_ongoing_or_started_and_not_completed:
            LOG.info("Found flow cell ready to be checked: %s!", flow_cell_obj.path)
            checked_flow_cells.append(flow_cell_obj)
            if not flow_cell_obj.passed_check:
                LOG.warning("Invalid flow cell directory found: %s", flow_cell_obj.path)
                if dry_run:
                    continue
                LOG.warning("Removing %s!", flow_cell_obj.path)
                flow_cell_obj.remove_failed_flow_cell()
        else:
            LOG.warning("Skipping check!")

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
            flow_cell.files_exist_on_disk,
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


@clean.command("fix-flow-cell-status")
@DRY_RUN
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
            if flow_cell.name in physical_ondisk_flow_cell_names
            else FlowCellStatus.REMOVED
        )
        if status_db_flow_cell_status != new_status:
            LOG.info(
                "Setting status of flow cell %s from %s to %s",
                flow_cell.name,
                status_db_flow_cell_status,
                new_status,
            )
            if dry_run:
                continue
            flow_cell.status = new_status
            status_db.commit()


@clean.command("remove-old-flow-cell-run-dirs")
@click.option(
    "-s",
    "--sequencer",
    type=click.Choice([Sequencers.HISEQX, Sequencers.HISEQGA, Sequencers.NOVASEQ, Sequencers.ALL]),
    default="all",
    help="Specify the sequencer. Default is to remove flow cells for all sequencers",
)
@click.option(
    "-o",
    "--days-old",
    type=int,
    default=21,
    help="Specify the age in days of the flow cells to be removed. Default is 21 days.",
)
@DRY_RUN
@click.pass_obj
def remove_old_flow_cell_run_dirs(context: CGConfig, sequencer: str, days_old: int, dry_run: bool):
    """Removes flow cells from flow cell run dir based on the sequencing date and
    the sequencer type, if specified"""
    status_db: Store = context.status_db
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    if sequencer == Sequencers.ALL:
        LOG.info("Checking flow cells for all sequencers!")
        for sequencer, run_directory in context.clean.flow_cells.flow_cell_run_dirs:
            LOG.info("Checking directory %s of sequencer %s:", run_directory, sequencer)
            clean_run_directories(days_old, dry_run, housekeeper_api, run_directory, status_db)

    else:
        run_directory = dict(context.clean.flow_cells.flow_cell_run_dirs).get(sequencer)
        LOG.info(
            "Checking directory %s of sequencer %s:",
            run_directory,
            sequencer,
        )
        clean_run_directories(days_old, dry_run, housekeeper_api, run_directory, status_db)


def clean_run_directories(days_old, dry_run, housekeeper_api, run_directory, status_db):
    """Cleans up all flow cell directories in the specified run directory"""
    flow_cell_dirs: List[Path] = [item for item in Path(run_directory).iterdir() if item.is_dir()]
    for flow_cell_dir in flow_cell_dirs:
        LOG.info("Checking flow cell %s", flow_cell_dir.name)
        run_dir_flow_cell = RunDirFlowCell(flow_cell_dir, status_db, housekeeper_api)
        if run_dir_flow_cell.exists_in_statusdb and run_dir_flow_cell.is_retrieved_from_pdc:
            LOG.info(
                "Skipping removal of flow cell %s, PDC retrieval status is '%s'!",
                flow_cell_dir,
                run_dir_flow_cell.flow_cell_status,
            )
            continue
        if run_dir_flow_cell.age < days_old:
            LOG.info(
                "Flow cell %s is %s days old and will NOT be removed.",
                flow_cell_dir,
                run_dir_flow_cell.age,
            )
            continue
        LOG.info(
            "Flow cell %s is %s days old and will be removed.",
            flow_cell_dir,
            run_dir_flow_cell.age,
        )
        if dry_run:
            continue
        LOG.info("Removing flow cell run directory %s.", run_dir_flow_cell.flow_cell_dir)
        run_dir_flow_cell.archive_sample_sheet()
        run_dir_flow_cell.remove_run_directory()
