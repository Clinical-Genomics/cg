"""cg module for cleaning databases and files."""

import logging
from datetime import timedelta
from pathlib import Path

import rich_click as click
from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.scout.scout_export import ScoutExportCase
from cg.apps.scout.scoutapi import ScoutAPI
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import (
    balsamic_past_run_dirs,
    balsamic_pon_past_run_dirs,
    balsamic_umi_past_run_dirs,
    fluffy_past_run_dirs,
    microsalt_past_run_dirs,
    mip_dna_past_run_dirs,
    mip_rna_past_run_dirs,
    mutant_past_run_dirs,
    rnafusion_past_run_dirs,
    rsync_past_run_dirs,
    tower_past_run_dirs,
)
from cg.constants.cli_options import DRY_RUN, SKIP_CONFIRMATION
from cg.constants.housekeeper_tags import AlignmentFileTag, ScoutTag
from cg.exc import FlowCellError, IlluminaCleanRunError
from cg.meta.clean.api import CleanAPI
from cg.meta.clean.clean_retrieved_spring_files import CleanRetrievedSpringFilesAPI
from cg.models.cg_config import CGConfig
from cg.services.illumina.cleaning.clean_runs_service import IlluminaCleanRunsService
from cg.utils.date import get_date_days_ago, get_timedelta_from_date
from cg.utils.files import get_directories_in_path

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


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def clean():
    """Clean up processes."""
    return


for sub_cmd in [
    balsamic_past_run_dirs,
    balsamic_umi_past_run_dirs,
    balsamic_pon_past_run_dirs,
    fluffy_past_run_dirs,
    mip_dna_past_run_dirs,
    mip_rna_past_run_dirs,
    mutant_past_run_dirs,
    rnafusion_past_run_dirs,
    rsync_past_run_dirs,
    microsalt_past_run_dirs,
    tower_past_run_dirs,
]:
    clean.add_command(sub_cmd)


@clean.command("hk-alignment-files")
@click.argument("bundle")
@DRY_RUN
@SKIP_CONFIRMATION
@click.pass_obj
def hk_alignment_files(
    context: CGConfig, bundle: str, skip_confirmation: bool = False, dry_run: bool = False
) -> None:
    """Clean up alignment files in Housekeeper bundle."""
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    for tag in AlignmentFileTag.file_tags():
        tag_files = set(housekeeper_api.get_files(bundle=bundle, tags=[tag]))

        if not tag_files:
            LOG.debug(
                f"Could not find any files ready for cleaning for bundle {bundle} and tag {tag}"
            )

        for hk_file in tag_files:
            if not (skip_confirmation or click.confirm(_get_confirm_question(bundle, hk_file))):
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
    context: click.Context, days_old: int, skip_confirmation: bool = False, dry_run: bool = False
) -> None:
    """Clean up of solved and archived Scout cases."""
    scout_api: ScoutAPI = context.obj.scout_api_37
    bundles: list[str] = []
    for status in [ScoutTag.ARCHIVED, ScoutTag.SOLVED]:
        cases: list[ScoutExportCase] = scout_api.get_cases(status=status, reruns=False)
        cases_added: int = 0
        for case in cases:
            analysis_time_delta: timedelta = get_timedelta_from_date(date=case.analysis_date)
            if analysis_time_delta.days > days_old:
                bundles.append(case.id)
                cases_added += 1
        LOG.info(f"{cases_added} cases marked for alignment files removal")

    for bundle in bundles:
        context.invoke(
            hk_alignment_files, bundle=bundle, skip_confirmation=skip_confirmation, dry_run=dry_run
        )


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
    """Clean up all non-protected files for all workflows."""
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


@clean.command("illumina-runs")
@DRY_RUN
@click.option(
    "--day-threshold", type=int, required=True, help="Number of days before a run can be deleted."
)
@click.pass_obj
def clean_illumina_runs(context: CGConfig, day_threshold: int, dry_run: bool):
    """Remove Illumina sequencing and demultiplexed runs from hasta."""

    directories_to_check: list[Path] = []
    for path in [
        Path(context.data_input.input_dir_path),
        Path(context.run_instruments.illumina.sequencing_runs_dir),
        Path(context.run_instruments.illumina.demultiplexed_runs_dir),
        Path(context.encryption.encryption_dir),
    ]:
        directories_to_check.extend(get_directories_in_path(path))
    for flow_cell_directory in directories_to_check:
        try:
            clean_service = IlluminaCleanRunsService(
                sequencing_run_path=flow_cell_directory,
                status_db=context.status_db,
                housekeeper_api=context.housekeeper_api,
                dry_run=dry_run,
            )
            clean_service.delete_run_directory(day_threshold)
        except (IlluminaCleanRunError, FlowCellError) as error:
            LOG.error(repr(error))
            continue


@clean.command("retrieved-spring-files")
@click.option(
    "--age-limit",
    type=int,
    default=7,
    help="Clean all Spring files which were retrieved more than given amount of days ago.",
    show_default=True,
)
@DRY_RUN
@click.pass_obj
def clean_retrieved_spring_files(context: CGConfig, age_limit: int, dry_run: bool):
    """Clean Spring files which were retrieved more than given amount of days ago."""
    clean_retrieved_spring_files_api = CleanRetrievedSpringFilesAPI(
        housekeeper_api=context.housekeeper_api, dry_run=dry_run
    )
    clean_retrieved_spring_files_api.clean_retrieved_spring_files(age_limit)


def _get_confirm_question(bundle, file_obj) -> str:
    """Return confirmation question."""
    return (
        f"{bundle}: remove file from file system and database: {file_obj.full_path}"
        if file_obj.is_included
        else f"{bundle}: remove file from database: {file_obj.full_path}"
    )
