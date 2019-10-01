""" Add CLI support to start MIP rare disease RNA"""
import logging

import click
from cg.apps import tb
from cg.apps.environ import environ_email
from cg.apps.mip import rdrna
from cg.cli.analysis import config as mip_cli_config
from cg.store import Store

LOGGER = logging.getLogger(__name__)


@click.group()
@click.pass_context
def rna(context):
    """ Run rare disease RNA workflow """
    context.obj['db'] = Store(context.obj['database'])
    context.obj['tb_api'] = tb.TrailblazerAPI(context.obj)
    context.obj['rna_api'] = rdrna.MipRDRNAAPI(context.obj['trailblazer']['script'])


@rna.command()
@click.option('-d', '--dry', is_flag=True, help='print command to console')
@click.option('-e', '--email', help='email to send errors to')
@click.option('-p', '--priority', type=click.Choice(['low', 'normal', 'high']))
@click.option('-sw', '--start-with', help='start mip from this program.')
@click.option('--skip-evaluation', is_flag=True, default=False, help='skip QC Collect')
@click.argument('case_id')
@click.pass_context
def start(context: click.Context, case_id: str, dry: bool = False,
          priority: str = None, email: str = None, start_with: str = None,
          skip_evaluation: bool = False):
    """Start the analysis pipeline for a case."""
    case_obj = context.obj['db'].family(case_id)
    if case_obj is None:
        LOGGER.error("%s: case not found", case_id)
        context.abort()
    if context.obj['tb_api'].analyses(family=case_obj.internal_id, temp=True).first():
        LOGGER.warning("%s: analysis already running", case_obj.internal_id)
    else:
        email = email or environ_email()
        # TODO move mip_config to it's own mip section in cg.yaml
        kwargs = dict(config=context.obj['trailblazer']['mip_config'], case=case_id,
                      priority=priority, email=email, dryrun=dry, start_with=start_with)
        if skip_evaluation:
            kwargs['skip_evaluation'] = True
        if dry:
            command = context.obj['rna_api'].build_command(**kwargs)
            print(command)
        else:
            context.obj['tb_api'].mark_analysis_pending(case_id=case_id, email=email)
            context.obj['rna_api'].start(**kwargs)


rna.add_command(mip_cli_config, 'pedigree')
