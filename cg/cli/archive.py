from typing import Optional

import click

from cg.constants.constants import DRY_RUN
from cg.meta.archive.archive import SpringArchiveAPI
from cg.models.cg_config import CGConfig


@click.group()
@click.pass_obj
def archive():
    """Archive utilities"""
    pass


@archive.command("archive-all-non-archived-files")
@click.option("-l", "--limit", help="Give a maximum amount of files to archive.")
@DRY_RUN
@click.pass_obj
def archive_all_non_archived_files(context: CGConfig, limit: Optional[int] = None):
    """Archives all non-archived spring files. If a limit is specified, the number of files to archive is capped."""
    spring_archive_api: SpringArchiveAPI = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow_config,
    )
    spring_archive_api.archive_all_non_archived_spring_files(spring_file_count_limit=limit)


@archive.command("update-job-statuses")
@click.option(help="Update statuses for all ongoing archivals and retrievals.")
@DRY_RUN
@click.pass_obj
def update_job_statuses(context: CGConfig):
    """Query an ongoing archival job and update Housekeeper if it is finished."""
    spring_archive_api: SpringArchiveAPI = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow_config,
    )
    spring_archive_api.update_statuses_for_ongoing_tasks()
