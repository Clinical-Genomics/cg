"""Cli commands for syncing items the status database"""
import logging

import click
from cg.store import Store

from cg.store.api.sync import sync_apptags

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def sync(context):
    """Sync information in the database."""
    context.obj['status'] = Store(context.obj['database'])


@sync.command('apptag')
@click.argument('excel_path')
@click.argument('prep-category')
@click.argument('signature')
@click.option('-s', '--sheet-name', default='Drop down list', help='(optional) name of sheet where '
                                                                   'to find the applications')
@click.option('-n', '--tag-column', default=2, help='(optional) zero-based column where to find '
                                                    'the applications')
@click.option('-a', '--activate', is_flag=True, help='Activate archived tags found in the '
                                                     'orderform')
@click.option('-i', '--inactivate', is_flag=True, help='Inactivate tags not found in the orderform')
@click.pass_context
def apptag(context, excel_path, prep_category, signature, sheet_name, tag_column, activate,
           inactivate):
    """Sync apptags in the status-db, will run as dry-run by default"""
    sync_apptags(context.obj['status'], excel_path, prep_category, signature, sheet_name,
                 tag_column, activate, inactivate)
