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
    context.obj['lims_api'] = lims.LimsAPI(context.obj)

@microsalt.command()
@click.option('--project', 'project_id', help='link all samples for a family')
@click.argument('sample_id', required=False)
def parameter(context, project_id, sample_id):
    """Link FASTQ files for a SAMPLE_ID."""
    if project_id and (sample_id is None):
        # link all samples in a family
        family_obj = context.obj['db'].family(project_id)
        link_objs = family_obj.links
    elif sample_id and (project_id is None):
        # link sample in all its families
        sample_obj = context.obj['db'].sample(sample_id)
        link_objs = sample_obj.links
    elif sample_id and project_id:
        # link only one sample in a family
        link_objs = [context.obj['db'].link(project_id, sample_id)]
    else:
        LOGGER.error('provide project and/or sample')
        context.abort()

    
