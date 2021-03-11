"""Cli commands for importing data into the status database"""
import logging
import getpass
from pathlib import Path

import click
from cg.constants import PREP_CATEGORIES
from cg.store import Store
from cg.store.api.import_func import (
    import_application_versions,
    import_applications,
    import_apptags,
)
from cg.utils.click.EnumChoice import EnumChoice

LOG = logging.getLogger(__name__)


@click.group("import")
@click.pass_context
def import_cmd(context):
    """Import information into the database."""
    context.obj["status_db"] = Store(context.obj["database"])


@import_cmd.command("application")
@click.argument("excel_path")
@click.argument("signature", required=False)
@click.option(
    "-d", "--dry-run", "dry_run", is_flag=True, help="Test run, no changes to the " "database"
)
@click.option("-s", "--sheet-name", help="Sheet name in workbook")
@click.pass_context
def application(context, excel_path, signature, sheet_name, dry_run):
    """Import new applications to status-db"""

    if not signature:
        signature = getpass.getuser()

    import_applications(context.obj["status_db"], excel_path, signature, dry_run, sheet_name)


@import_cmd.command("application-version")
@click.argument("excel_path")
@click.argument("signature", required=False)
@click.option(
    "-d", "--dry-run", "dry_run", is_flag=True, help="Test run, no changes to the " "database"
)
@click.option(
    "--skip-missing", "skip_missing", is_flag=True, help="continue despite missing " "applications"
)
@click.pass_context
def application_version(context, excel_path, signature, dry_run, skip_missing):
    """Import new application versions to status-db"""

    if not signature:
        signature = getpass.getuser()

    import_application_versions(
        context.obj["status_db"], excel_path, signature, dry_run, skip_missing
    )


@import_cmd.command("apptag")
@click.argument("excel_path", type=click.types.Path(exists=True, file_okay=True, dir_okay=False))
@click.argument("prep-category", type=click.types.Choice(PREP_CATEGORIES))
@click.argument("signature", required=False, type=click.types.STRING)
@click.option(
    "-s",
    "--sheet-name",
    default="Drop down list",
    help="(optional) name of sheet where to find the applications",
)
@click.option(
    "-c",
    "--tag-column",
    default=2,
    help="(optional) zero-based column where to find the applications",
    type=click.types.INT,
)
@click.option(
    "-r",
    "--tag-row",
    default=0,
    help="(optional) zero-based row where to start looking for the applications",
    type=click.types.INT,
)
@click.option(
    "-a", "--activate", is_flag=True, help="Activate archived tags found in the " "orderform"
)
@click.option("-i", "--inactivate", is_flag=True, help="Inactivate tags not found in the orderform")
@click.pass_context
def apptag(
    context: click.Context,
    excel_path: Path,
    prep_category: str,
    signature: str,
    sheet_name: str,
    tag_column: int,
    tag_row: int,
    activate: bool,
    inactivate: bool,
):
    """
    Syncs all applications from the specified excel file
    Args:
        :param inactivate:          Inactivate tags not found in the orderform
        :param activate:            Activate archived tags found in the orderform
        :param sheet_name:          (optional) name of sheet where the applications can be found
        :param tag_column:          (optional) zero-based column where the application tags can be
        found
        :param tag_row:             (optional) zero-based row where the application tags can be
        found
        :param prep_category:       prep_category to sync
        :param excel_path:          Path to orderform excel file
        :param signature:           Signature of user running the script
    """

    if not signature:
        signature = getpass.getuser()

    import_apptags(
        store=context.obj["status_db"],
        excel_path=excel_path,
        prep_category=prep_category,
        signature=signature,
        sheet_name=sheet_name,
        tag_column=tag_column,
        tag_row=tag_row,
        activate=activate,
        inactivate=inactivate,
    )
