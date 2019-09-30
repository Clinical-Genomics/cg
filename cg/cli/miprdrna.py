""" Add CLI support to start MIP rare disease RNA"""
import logging

import click
from cg.apps import hk
from cg.cli.analysis import config as mip_cli_config
from cg.store import Store

LOGGER = logging.getLogger(__name__)


@click.group()
@click.pass_context
def rna(context):
    """ Run rare disease RNA workflow """
    context.obj['hk'] = hk.HousekeeperAPI(context.obj)
    context.obj['db'] = Store(context.obj['database'])


@rna.command()
@click.option('-p', '--priority', type=click.Choice(['low', 'normal', 'high']))
@click.option('-e', '--email', help='email to send errors to')
@click.option('-sw', '--start-with', help='start mip from this program.')
@click.argument('case_id')
@click.pass_context
def start(context: click.Context, case_id: str, priority: str = None, email: str = None,
          start_with: str = None):
    """Start the analysis pipeline for a case."""
    case_obj = context.obj['db'].family(case_id)
    if case_obj is None:
        LOGGER.error("%s: case not found", case_id)
        context.abort()
    if context.obj['tb'].analyses(family=case_obj.internal_id, temp=True).first():
        LOGGER.warning("%s: analysis already running", case_obj.internal_id)
    else:
        context.obj['api'].start(case_obj, priority=priority, email=email, start_with=start_with)


rna.add_command(mip_cli_config)
