import click
from click.core import ParameterSource

from cg.constants.archiving import DEFAULT_SPRING_ARCHIVE_COUNT
from cg.constants.constants import DRY_RUN
from cg.meta.archive.archive import SpringArchiveAPI
from cg.models.cg_config import CGConfig


@click.group()
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
        click.echo(
            "Incorrect input parameters - please do not provide both a limit and set --archive-all."
        )
        raise click.Abort

    spring_archive_api = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow,
    )
    spring_archive_api.archive_spring_files_and_add_archives_to_housekeeper(
        spring_file_count_limit=None if archive_all else limit
    )


@archive.command("update-job-statuses")
@click.pass_obj
def update_job_statuses(context: CGConfig):
    """Queries ongoing jobs and updates Housekeeper."""
    spring_archive_api = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow,
    )
    spring_archive_api.update_statuses_for_ongoing_tasks()


@archive.command("delete-file")
@DRY_RUN
@click.pass_obj
@click.argument("file_path", required=True)
def delete_file(context: CGConfig, dry_run: bool, file_path: str):
    """Delete an archived file and remove it from Housekeeper.
    The file will not be deleted if it is not confirmed archived.
    The file will not be deleted if its archive location can not be determined from the file tags.
    """
    spring_archive_api = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow,
    )
    spring_archive_api.delete_file(file_path=file_path, dry_run=dry_run)
