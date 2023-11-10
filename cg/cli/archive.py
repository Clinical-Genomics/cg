import logging

import click
from click.core import ParameterSource

from cg.constants.constants import DRY_RUN
from cg.meta.archive.archive import SpringArchiveAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)
DEFAULT_SPRING_ARCHIVE_COUNT = 200


@click.group()
@click.pass_obj
def archive():
    """Archive utilities."""
    pass


@archive.command("archive-spring-files")
@click.option(
    "-l",
    "--limit",
    help="Give a limit to the amount of files to archive.",
    default=DEFAULT_SPRING_ARCHIVE_COUNT,
    show_default=True,
)
@click.option(
    "--archive-all",
    help="Use in order to archive all non-archived-files",
    is_flag=True,
    default=False,
    show_default=True,
)
@DRY_RUN
@click.pass_obj
def archive_spring_files(context: CGConfig, limit: int | None, archive_all: bool):
    """Archives non-archived spring files.
    Raises:
        click.Abort if both a limit to the number of spring files to archive and archive_all is specified.
    """

    if (
        click.get_current_context().get_parameter_source("limit") == ParameterSource.COMMANDLINE
        and limit
        and archive_all
    ):
        LOG.warning(
            "Incorrect input parameters - please do not provide both a limit and set --archive-all to true."
        )
        raise click.Abort

    spring_archive_api = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow_config,
    )
    spring_archive_api.archive_all_non_archived_spring_files(
        spring_file_count_limit=None if archive_all else limit
    )


@archive.command("update-job-statuses")
@click.option(help="Update statuses for all ongoing archivals and retrievals.")
@DRY_RUN
@click.pass_obj
def update_job_statuses(context: CGConfig):
    """Queries ongoing jobs and updates Housekeeper for the ones that have finished."""
    spring_archive_api = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow_config,
    )
    spring_archive_api.update_statuses_for_ongoing_tasks()
