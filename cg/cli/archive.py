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
def archive_all_non_archived_files(context: CGConfig, dry_run: bool, limit: Optional[int] = None):
    """Archives all non-archived spring files. If a limit is specified, the number of files to archive is capped."""
    spring_archive_api: SpringArchiveAPI = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow_config,
    )
    spring_archive_api.archive_all_non_archived_spring_files(spring_file_count_limit=limit)


@archive.command("retrieve-file")
@click.option("--file-path", help="Retrieve a specific file.")
@DRY_RUN
@click.pass_obj
def retrieve_file(context: CGConfig, dry_run: bool, file_path: str):
    """Submits a retrieval task for the specified file."""
    spring_archive_api: SpringArchiveAPI = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow_config,
    )


@archive.command("retrieve-sample")
@click.option("-s", "--sample-internal-id", help="Retrieve a specific sample, ex. 'updog'.")
@DRY_RUN
@click.pass_obj
def retrieve_sample(context: CGConfig, dry_run: bool, sample_internal_id: str):
    """Submits a retrieval task for the specified sample."""
    spring_archive_api: SpringArchiveAPI = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow_config,
    )


@archive.command("retrieve-flowcell")
@click.option("--flow-cell", help="Retrieve all samples run on a specific flow cell.")
@DRY_RUN
@click.pass_obj
def retrieve_flow_cell(context: CGConfig, dry_run: bool, flow_cell: str):
    """Submits a retrieval task for the samples run on the specified flow cell."""
    spring_archive_api: SpringArchiveAPI = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow_config,
    )


@archive.command("update-archival-status")
@click.option("-j", "--job-id", help="Update status for an ongoing archival.")
@DRY_RUN
@click.pass_obj
def update_job_status(context: CGConfig, dry_run: bool, job_id: int):
    """Query an ongoing archival job and update Housekeeper if it is finished."""
    spring_archive_api: SpringArchiveAPI = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow_config,
    )


@archive.command("update-retrieval-status")
@click.option("-j", "--job-id", help="Update status for an ongoing retrieval.")
@DRY_RUN
@click.pass_obj
def update_job_status(context: CGConfig, dry_run: bool, job_id: int):
    """Query an ongoing retrieval job and update Housekeeper if it is finished."""
    spring_archive_api: SpringArchiveAPI = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow_config,
    )
