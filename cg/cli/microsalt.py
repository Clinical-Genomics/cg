""" Add CLI support to start microSALT """
import logging
#import subprocess
from pathlib import Path

import click
from cg.apps import hk, lims
from cg.meta.analysis import AnalysisAPI
from cg.store import Store
from cg.apps.usalt.fastq import USaltFastqHandler
from cg.exc import LimsDataError

LOGGER = logging.getLogger(__name__)


@click.group()
@click.pass_context
def microsalt(context):
    """ Run microbial workflow """
    context.obj['hk'] = hk.HousekeeperAPI(context.obj)
    context.obj['db'] = Store(context.obj['database'])
    context.obj['lims'] = lims.LimsAPI(context.obj)

@microsalt.command()
@click.option('--project', 'project_id', help='link all samples for a family')
@click.argument('sample_id', required=False)
def parameter(context, project_id, sample_id):
    """ Get all samples for a project """
    if project_id and (sample_id is None):
        sample_ids = context.obj['lims'].get_samples(project_id=project_id)
    elif sample_id and (project_id is None):
        sample_objs = [context.obj['db'].sample(sample_id)]
    elif sample_id and project_id:
        # link only one sample in a family
        link_objs = [context.obj['lims'].get_samples(project_id, sample_id)]
    else:
        LOGGER.error('provide project and/or sample')
        context.abort()

    
@microsalt.command()
@click.option('-d', '--dry', is_flag=True, help='print command to console')
@click.option('-p', '--parameters', required=False, help='Optional')
#@click.option('-p', '--priority', default='low', type=click.Choice(['low', 'normal', 'high']))
#@click.option('-e', '--email', help='email to send errors to')
@click.argument('project_id')
@click.pass_context
def run(context, dry, parameters, project_id):
    pass
