"""Cli commands for importing data into the status database"""
import logging

import click
from cg.store import Store

from cg.store.api.import_func import import_application_versions, import_applications

LOG = logging.getLogger(__name__)


@click.group('import')
@click.pass_context
def import_cmd(context):
    """Import information into the database."""
    context.obj['status'] = Store(context.obj['database'])


@import_cmd.command('application')
@click.argument('excel_path')
@click.argument('signature')
@click.option('-d', '--dry-run', 'dry_run', is_flag=True, help='Test run, no changes to the '
                                                               'database')
@click.option('-s', '--sheet-name', help='Sheet name in workbook')
@click.pass_context
def application(context, excel_path, signature, sheet_name, dry_run):
    """Import new applications to status-db"""
    import_applications(context.obj['status'], excel_path, signature, dry_run, sheet_name)


@import_cmd.command('application-version')
@click.argument('excel_path')
@click.argument('signature')
@click.option('-d', '--dry-run', 'dry_run', is_flag=True, help='Test run, no changes to the '
                                                               'database')
@click.option('--skip-missing', 'skip_missing', is_flag=True, help='continue despite missing '
                                                                   'applications')
@click.pass_context
def application_version(context, excel_path, signature, dry_run, skip_missing):
    """Import new application versions to status-db"""
    import_application_versions(context.obj['status'], excel_path, signature, dry_run, skip_missing)
