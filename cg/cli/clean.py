"""cg module for cleaning databases and files."""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import click
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.scout.scout_export import ScoutExportCase
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.cli.workflow.commands import (
    balsamic_past_run_dirs,
    balsamic_pon_past_run_dirs,
    balsamic_qc_past_run_dirs,
    balsamic_umi_past_run_dirs,
    fluffy_past_run_dirs,
    microsalt_past_run_dirs,
    mip_dna_past_run_dirs,
    mip_rna_past_run_dirs,
    mutant_past_run_dirs,
    rnafusion_past_run_dirs,
    rsync_past_run_dirs,
)
from cg.constants import FlowCellStatus
from cg.constants.constants import DRY_RUN, SKIP_CONFIRMATION
from cg.constants.housekeeper_tags import ALIGNMENT_FILE_TAGS, ScoutTag, SequencingFileTag
from cg.constants.sequencing import Sequencers
from cg.exc import FlowCellError, HousekeeperBundleVersionMissingError
from cg.meta.clean.api import CleanAPI
from cg.meta.clean.demultiplexed_flow_cells import DemultiplexedRunsFlowCell
from cg.meta.clean.flow_cell_run_directories import RunDirFlowCell
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData as DemultiplexFlowCell
from cg.store import Store
from cg.store.models import Analysis, Flowcell, Sample
from cg.utils.date import get_date_days_ago, get_timedelta_from_date
from cg.utils.dispatcher import Dispatcher
from cgmodels.cg.constants import Pipeline
from housekeeper.store.models import File, Version
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query
from tabulate import tabulate

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
    """Clean up processes."""
    return


for sub_cmd in [
    balsamic_past_run_dirs,
    balsamic_qc_past_run_dirs,
    balsamic_umi_past_run_dirs,
    balsamic_pon_past_run_dirs,
    fluffy_past_run_dirs,
    mip_dna_past_run_dirs,
    mip_rna_past_run_dirs,
    mutant_past_run_dirs,
    rnafusion_past_run_dirs,
    rsync_past_run_dirs,
    microsalt_past_run_dirs,
]:
    clean.add_command(sub_cmd)


@clean.command("hk-alignment-files")
@click.argument("bundle")
@DRY_RUN
@SKIP_CONFIRMATION
@click.pass_obj
def hk_alignment_files(
    context: CGConfig, bundle: str, yes: bool = False, dry_run: bool = False
) -> None:
    """Clean up alignment files in Housekeeper bundle."""
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    for tag in ALIGNMENT_FILE_TAGS:
        tag_files = set(housekeeper_api.get_files(bundle=bundle, tags=[tag]))

        if not tag_files:
            LOG.warning(
                f"Could not find any files ready for cleaning for bundle {bundle} and tag {tag}"
            )

        for hk_file in tag_files:
            if not (yes or click.confirm(_get_confirm_question(bundle, hk_file))):
                continue

            file_path: Path = Path(hk_file.full_path)
            if hk_file.is_included and file_path.exists():
                LOG.info(f"Unlinking {file_path}")
                if not dry_run:
                    file_path.unlink()

            LOG.info(f"Deleting {file_path} from database")
            if not dry_run:
                housekeeper_api.delete_file(file_id=hk_file.id)
                housekeeper_api.commit()


@clean.command("scout-finished-cases")
@click.option(
    "--days-old",
    type=int,
    default=300,
    help="Clean alignment files with analysis dates older then given number of days",
)
@SKIP_CONFIRMATION
@DRY_RUN
@click.pass_context
def scout_finished_cases(
    context: click.Context, days_old: int, yes: bool = False, dry_run: bool = False
) -> None:
    """Clean up of solved and archived Scout cases."""
    scout_api: ScoutAPI = context.obj.scout_api
    bundles: List[str] = []
    for status in [ScoutTag.ARCHIVED.value, ScoutTag.SOLVED.value]:
        cases: List[ScoutExportCase] = scout_api.get_cases(status=status, reruns=False)
        cases_added: int = 0
        for case in cases:
            analysis_time_delta: timedelta = get_timedelta_from_date(date=case.analysis_date)
            if analysis_time_delta.days > days_old:
                bundles.append(case.id)
                cases_added += 1
        LOG.info(f"{cases_added} cases marked for alignment files removal")

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
def hk_case_bundle_files(context: CGConfig, days_old: int, dry_run: bool = False) -> None:
    """Clean up all non-protected files for all pipelines."""
    housekeeper_api: HousekeeperAPI = context.obj.housekeeper_api
    clean_api: CleanAPI = CleanAPI(status_db=context.obj.status_db, housekeeper_api=housekeeper_api)

    size_cleaned: int = 0
    version_file: File
    for version_file in clean_api.get_unprotected_existing_bundle_files(
        before=get_date_days_ago(days_ago=days_old)
    ):
        file_path: Path = Path(version_file.full_path)
        file_size: int = file_path.stat().st_size
        size_cleaned += file_size
        if dry_run:
            LOG.info(f"Dry run: {dry_run}. Keeping file {file_path}")
            continue

        file_path.unlink()
        housekeeper_api.delete_file(file_id=version_file.id)
        housekeeper_api.commit()
        LOG.info(f"Removed file {file_path}. Dry run: {dry_run}")

    LOG.info(f"Process freed {round(size_cleaned * 0.0000000001, 2)} GB. Dry run: {dry_run}")


@clean.command("hk-bundle-files")
@click.option("-c", "--case-id", type=str, required=False)
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
    """Remove files found in Housekeeper bundles."""

    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    status_db: Store = context.status_db

    date_threshold: datetime = get_date_days_ago(days_ago=days_old)

    function_dispatcher: Dispatcher = Dispatcher(
        functions=[
            status_db.get_analyses_started_at_before,
            status_db.get_analyses_for_case_and_pipeline_started_at_before,
            status_db.get_analyses_for_pipeline_started_at_before,
            status_db.get_analyses_for_case_started_at_before,
        ],
        input_dict={
            "case_internal_id": case_id,
            "pipeline": pipeline,
            "started_at_before": date_threshold,
        },
    )
    analyses: List[Analysis] = function_dispatcher()

    size_cleaned: int = 0
    for analysis in analyses:
        LOG.info(f"Cleaning analysis {analysis}")
        bundle_name: str = analysis.family.internal_id
        hk_bundle_version: Optional[Version] = housekeeper_api.version(
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
        version_files: List[File] = housekeeper_api.get_files(
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
    search: str = f"%{demux_api.out_dir}%"
    fastq_files_in_housekeeper: Query = housekeeper_api.files(
        tags=[SequencingFileTag.FASTQ]
    ).filter(File.path.like(search))
    spring_files_in_housekeeper: Query = housekeeper_api.files(
        tags=[SequencingFileTag.SPRING]
    ).filter(File.path.like(search))
    for flow_cell_dir in demux_api.out_dir.iterdir():
        flow_cell: DemultiplexedRunsFlowCell = DemultiplexedRunsFlowCell(
            flow_cell_path=flow_cell_dir,
            status_db=status_db,
            housekeeper_api=housekeeper_api,
            trailblazer_api=trailblazer_api,
            sample_sheets_dir=sample_sheets_dir,
            fastq_files=fastq_files_in_housekeeper,
            spring_files=spring_files_in_housekeeper,
        )
        if not flow_cell.is_demultiplexing_ongoing_or_started_and_not_completed:
            LOG.info(f"Found flow cell ready to be checked: {flow_cell.path}!")
            checked_flow_cells.append(flow_cell)
            if not flow_cell.passed_check:
                LOG.warning(f"Invalid flow cell directory found: {flow_cell.path}")
                if dry_run:
                    continue
                LOG.warning(f"Removing {flow_cell.path}!")
                flow_cell.remove_failed_flow_cell()
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
    """Set correct flow cell statuses in Statusdb."""
    status_db: Store = context.status_db
    housekeeper_api: HousekeeperAPI = context.housekeeper_api

    flow_cells_in_statusdb: List[Flowcell] = status_db.get_flow_cells_by_statuses(
        flow_cell_statuses=[FlowCellStatus.ON_DISK, FlowCellStatus.REMOVED]
    )

    LOG.info(
        f"Number of flow cells with status {FlowCellStatus.ON_DISK.value} or {FlowCellStatus.REMOVED} in Statusdb: {len(flow_cells_in_statusdb)}"
    )

    for flow_cell in flow_cells_in_statusdb:
        sample_bundle_names: List[str] = [sample.internal_id for sample in flow_cell.samples]
        are_sequencing_files_in_hk: bool = False
        are_sequencing_files_on_disk: bool = False
        try:
            are_sequencing_files_in_hk: bool = housekeeper_api.is_fastq_or_spring_in_all_bundles(
                bundle_names=sample_bundle_names
            )
            are_sequencing_files_on_disk: bool = (
                housekeeper_api.is_fastq_or_spring_on_disk_in_all_bundles(
                    bundle_names=sample_bundle_names
                )
            )
        except HousekeeperBundleVersionMissingError:
            LOG.warning(
                f"Cannot find sample bundle in Housekeeper for sample on flow cell: {flow_cell.name}"
            )
        new_status: str = (
            FlowCellStatus.ON_DISK
            if are_sequencing_files_in_hk and are_sequencing_files_on_disk
            else FlowCellStatus.REMOVED
        )

        if flow_cell.status != new_status:
            LOG.info(
                f"Setting status of flow cell {flow_cell.name} from: {flow_cell.status} to {new_status}"
            )
            if dry_run:
                continue
            flow_cell.status: str = new_status
            status_db.session.commit()


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
    help="Specify the age in days of the flow cells to be removed.",
)
@DRY_RUN
@click.pass_obj
def remove_old_flow_cell_run_dirs(context: CGConfig, sequencer: str, days_old: int, dry_run: bool):
    """Removes flow cells from flow cell run dir based on the sequencing date and
    the sequencer type, if specified."""
    status_db: Store = context.status_db
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    if sequencer == Sequencers.ALL:
        LOG.info("Checking flow cells for all sequencers!")
        for sequencer, run_directory in context.clean.flow_cells.flow_cell_run_dirs:
            LOG.info(f"Checking directory {run_directory} of sequencer {sequencer}:")
            flow_cell_dirs: List[Path] = [
                flow_cell_dir
                for flow_cell_dir in Path(run_directory).iterdir()
                if flow_cell_dir.is_dir()
            ]
            for flow_cell_dir in flow_cell_dirs:
                clean_run_directories(
                    days_old=days_old,
                    dry_run=dry_run,
                    housekeeper_api=housekeeper_api,
                    run_directory=flow_cell_dir,
                    status_db=status_db,
                )

    else:
        run_directory: str = dict(context.clean.flow_cells.flow_cell_run_dirs).get(sequencer)
        LOG.info(f"Checking directory {run_directory} of sequencer {sequencer}:")
        flow_cell_dirs: List[Path] = [
            flow_cell_dir
            for flow_cell_dir in Path(run_directory).iterdir()
            if flow_cell_dir.is_dir()
        ]
        for flow_cell_dir in flow_cell_dirs:
            clean_run_directories(
                days_old=days_old,
                dry_run=dry_run,
                housekeeper_api=housekeeper_api,
                run_directory=flow_cell_dir,
                status_db=status_db,
            )


@clean.command("remove-old-demutliplexed-run-dirs")
@click.option(
    "-o",
    "--days-old",
    type=int,
    default=21,
    help="Specify the age in days of the flow cells to be removed.",
)
@DRY_RUN
@click.pass_obj
def remove_old_demutliplexed_run_dirs(context: CGConfig, days_old: int, dry_run: bool):
    """Removes flow cells from demultiplexed run directory."""
    status_db: Store = context.status_db
    demux_api: DemultiplexingAPI = context.demultiplex_api
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    trailblazer_api: TrailblazerAPI = context.trailblazer_api
    for flow_cell_dir in demux_api.get_all_demultiplexed_flow_cell_dirs():
        try:
            flow_cell: DemultiplexFlowCell = DemultiplexFlowCell(flow_cell_path=flow_cell_dir)
        except FlowCellError:
            continue

        if not flow_cell.is_demultiplexing_complete:
            LOG.info(
                f"Demultiplexing not finished for {flow_cell.id}. Skipping removal of the directory."
            )
            continue

        samples: List[Sample] = status_db.get_samples_from_flow_cell(flow_cell_id=flow_cell.id)
        try:
            are_sequencing_files_in_hk: bool = housekeeper_api.is_fastq_or_spring_in_all_bundles(
                bundle_names=[sample.internal_id for sample in samples]
            )
        except HousekeeperBundleVersionMissingError:
            LOG.info(
                f"No bundle found for one or more of the samples on flow cell {flow_cell.id}."
                f" Skipping removal of the directory."
            )
            continue

        demux_runs_flow_cell: DemultiplexedRunsFlowCell = DemultiplexedRunsFlowCell(
            flow_cell_path=flow_cell_dir,
            status_db=status_db,
            housekeeper_api=housekeeper_api,
            trailblazer_api=trailblazer_api,
            sample_sheets_dir=context.clean.flow_cells.sample_sheets_dir_name,
        )
        if (
            not demux_runs_flow_cell.is_demultiplexing_ongoing_or_started_and_not_completed
            and are_sequencing_files_in_hk
        ):
            LOG.info(f"Found flow cell ready to be removed: {demux_runs_flow_cell.path}!")
            if dry_run:
                continue
            LOG.warning(f"Removing {demux_runs_flow_cell.path}!")
            clean_run_directories(
                days_old=days_old,
                dry_run=dry_run,
                housekeeper_api=housekeeper_api,
                run_directory=demux_runs_flow_cell.path,
                status_db=status_db,
            )


def clean_run_directories(
    days_old: int,
    dry_run: bool,
    housekeeper_api: HousekeeperAPI,
    run_directory: Path,
    status_db: Store,
):
    """Cleans up all flow cell directories in the specified run directory."""
    LOG.info(f"Checking flow cell {run_directory.name}")
    run_dir_flow_cell: RunDirFlowCell = RunDirFlowCell(
        flow_cell_dir=run_directory, status_db=status_db, housekeeper_api=housekeeper_api
    )
    if run_dir_flow_cell.exists_in_statusdb and run_dir_flow_cell.is_retrieved_from_pdc:
        LOG.info(
            f"Skipping removal of flow cell {run_directory}, PDC retrieval status is '{run_dir_flow_cell.flow_cell_status}'!"
        )
        return
    if run_dir_flow_cell.age < days_old:
        LOG.info(
            f"Flow cell {run_directory} is {run_dir_flow_cell.age} days old and will NOT be removed."
        )
        return
    LOG.info(f"Flow cell {run_directory} is {run_dir_flow_cell.age} days old and will be removed.")
    if dry_run:
        return
    LOG.info(f"Removing flow cell run directory {run_dir_flow_cell.flow_cell_dir}.")
    run_dir_flow_cell.archive_sample_sheet()
    run_dir_flow_cell.remove_run_directory()


def _get_confirm_question(bundle, file_obj) -> str:
    """Return confirmation question."""
    return (
        f"{bundle}: remove file from file system and database: {file_obj.full_path}"
        if file_obj.is_included
        else f"{bundle}: remove file from database: {file_obj.full_path}"
    )
