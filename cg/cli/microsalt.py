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
@click.pass_context
def parameter(context, project_id, sample_id):
    """ Get all samples for a project """
    if project_id and (sample_id is None):
        sample_objs = context.obj['db'].microbial_order(project_id).microbial_samples
    elif sample_id and (project_id is None):
        sample_objs = [context.obj['db'].microbial_sample(sample_id)]
    elif sample_id and project_id:
        sample_objs = [
            sample_obj for sample_obj
            in context.obj['db'].microbial_order(project_id).microbial_samples
            if sample_obj.internal_id == sample_id
        ]
    else:
        LOGGER.error('provide project and/or sample')
        context.abort()

    print(sample_objs)

    parameter = {}
    for sample_obj in sample_objs:
        parameter = {'CG_ID_project': sample_obj.microbial_order.internal_id,
                     'CG_ID_sample': sample_obj.internal_id,
                     'Customer_ID_sample': sample_obj.name,
                     'organism': sample_obj.organism.internal_id,
                     'priority': sample_obj.priority,
                     'reference': sample_obj.organism.reference_genome,
                     'Customer_ID': sample_obj.microbial_order.customer.internal_id,
                     'application_tag': sample_obj.application_version.application.tag,
                     #'date_arrival': date_arrival,
                     #'date_sequencing': date_sequencing,
                     #'date_libprep': date_libprep,
                     #'method_libprep': method_libprep,
                     #'method_sequencing': method_sequencing
                    }
    print(parameter)

@microsalt.command()
@click.option('-d', '--dry', is_flag=True, help='print command to console')
@click.option('-p', '--parameters', required=False, help='Optional')
#@click.option('-p', '--priority', default='low', type=click.Choice(['low', 'normal', 'high']))
#@click.option('-e', '--email', help='email to send errors to')
@click.argument('project_id')
@click.pass_context
def start(context, dry, parameters, project_id):
    pass
