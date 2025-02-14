import rich_click as click
from click.core import ParameterSource

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.constants.archiving import DEFAULT_SPRING_ARCHIVE_COUNT
from cg.constants.cli_options import DRY_RUN
from cg.meta.archive.archive import SpringArchiveAPI
from cg.models.cg_config import CGConfig


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
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


@archive.group("retrieve")
def retrieve_spring():
    """Retrieve spring files."""
    pass


@retrieve_spring.command("sample")
@click.pass_obj
@click.argument("sample_id", required=True)
def retrieve_spring_files_for_sample(context: CGConfig, sample_id: str):
    """Retrieve spring files for a sample."""
    spring_archive_api = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow,
    )
    spring_archive_api.retrieve_spring_files_for_sample(sample_id=sample_id)


@retrieve_spring.command("case")
@click.pass_obj
@click.argument("case_id", required=True)
def retrieve_spring_files_for_case(context: CGConfig, case_id: str):
    """Retrieve spring files for a case."""
    spring_archive_api = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow,
    )
    spring_archive_api.retrieve_spring_files_for_case(case_id=case_id)


@retrieve_spring.command("order")
@click.pass_obj
@click.option("-t", "--ticket_id", help="Specify ticket_id instead of order_id")
@click.argument("order_id", required=False)
def retrieve_spring_files_for_order(context: CGConfig, order_id: int = None, ticket_id: int = None):
    """Retrieve spring files for an order."""
    spring_archive_api = SpringArchiveAPI(
        status_db=context.status_db,
        housekeeper_api=context.housekeeper_api,
        data_flow_config=context.data_flow,
    )
    spring_archive_api.retrieve_spring_files_for_order(
        id_=order_id or ticket_id, is_order_id=order_id is not None
    )
