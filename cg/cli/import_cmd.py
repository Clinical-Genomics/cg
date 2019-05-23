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
@click.option('-e', '--excel_path', required=True,
              help='Path to excel with applications.')
@click.option('-s', '--sign', required=True,
              help='Signature.')
@click.pass_context
def application(context, excel_path, sign):
    """Import new applications to status-db"""
    import_applications(context.obj['status'], excel_path, sign)


@import_cmd.command('application-version')
@click.option('-e', '--excel_path', required=True,
              help='Path to excel with apptag versions.')
@click.option('-s', '--sign', required=True,
              help='Signature.')
@click.pass_context
def application_version(context, excel_path, sign):
    """Import new application versions to status-db"""
    import_application_versions(context.obj['status'], excel_path, sign)
