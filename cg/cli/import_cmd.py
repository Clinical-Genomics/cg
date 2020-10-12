"""Cli commands for importing data into the status database"""
import logging
import getpass

import click
from cg.store import Store
from cg.store.api.import_func import (
    import_application_versions,
    import_applications,
    import_apptags,
)

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
@click.argument("excel_path")
@click.argument("prep-category")
@click.argument("signature", required=False)
@click.option(
    "-s",
    "--sheet-name",
    default="Drop down list",
    help="(optional) name of sheet where " "to find the applications",
)
@click.option(
    "-n",
    "--tag-column",
    default=2,
    help="(optional) zero-based column where to find " "the applications",
)
@click.option(
    "-a", "--activate", is_flag=True, help="Activate archived tags found in the " "orderform"
)
@click.option("-i", "--inactivate", is_flag=True, help="Inactivate tags not found in the orderform")
@click.pass_context
def apptag(
    context, excel_path, prep_category, signature, sheet_name, tag_column, activate, inactivate
):
    """
    Syncs all applications from the specified excel file
    Args:
        :param inactivate:          Inactivate tags not found in the orderform
        :param activate:            Activate archived tags found in the orderform
        :param sheet_name:          (optional) name of sheet where the applications can be found
        :param tag_column:          (optional) zero-based column where the application tags can be
        found
        :param prep_category:       prep_category to sync
        :param store:               status database store
        :param excel_path:          Path to orderform excel file
        :param sign:                Signature of user running the script
    """

    if not signature:
        signature = getpass.getuser()

    import_apptags(
        context.obj["status_db"],
        excel_path,
        prep_category,
        signature,
        sheet_name,
        tag_column,
        activate,
        inactivate,
    )
