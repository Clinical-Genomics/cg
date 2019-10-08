""" Add CLI support to start MIP rare disease RNA"""
import logging

import click
from cg.apps import tb
from cg.apps.environ import environ_email
from cg.apps.mip import MipAPI
from cg.cli.analysis import case_config as mip_cli_config
from cg.store import Store

LOGGER = logging.getLogger(__name__)


@click.group()
@click.pass_context
def rna(context):
    """ Run rare disease RNA workflow """
    context.obj['db'] = Store(context.obj['database'])
    context.obj['tb_api'] = tb.TrailblazerAPI(context.obj)
    context.obj['rna_api'] = MipAPI(context.obj['mip-rd-rna']['script'],
                                    context.obj['mip-rd-rna']['pipeline'])


@rna.command()
@click.option('-d', '--dry', is_flag=True, help='print command to console')
@click.option('-e', '--email', help='email to send errors to')
@click.option('-p', '--priority', type=click.Choice(['low', 'normal', 'high']))
@click.option('-sw', '--start-with', help='start mip from this program.')
@click.argument('case_id')
@click.pass_context
def start(context: click.Context, case_id: str, dry: bool = False,
          priority: str = None, email: str = None, start_with: str = None):
    """Start the analysis pipeline for a case."""
    tb_api = context.obj['tb_api']
    rna_api = context.obj['rna_api']
    case_obj = context.obj['db'].family(case_id)
    if case_obj is None:
        LOGGER.error("%s: case not found", case_id)
        context.abort()
    if tb_api.analyses(family=case_obj.internal_id, temp=True).first():
        LOGGER.warning("%s: analysis already running", case_obj.internal_id)
    else:
        email = email or environ_email()
        kwargs = dict(config=context.obj['mip-rd-rna']['mip_config'], case=case_id,
                      priority=priority, email=email, dryrun=dry, start_with=start_with)
        if dry:
            command = rna_api.build_command(**kwargs)
            LOGGER.info(' '.join(command))
        else:
            rna_api.start(**kwargs)
            tb_api.mark_analyses_deleted(case_id=case_id)
            tb_api.add_pending(case_id, email=email)
            LOGGER.info('MIP started!')


rna.add_command(mip_cli_config, 'case-config')
