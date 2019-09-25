""" Add CLI support to start microSALT """
import json
import logging
#import subprocess
from pathlib import Path

import click
from cg.apps import hk, lims
from cg.store import Store

LOGGER = logging.getLogger(__name__)


@click.group()
@click.pass_context
def microsalt(context):
    """ Run microbial workflow """
    context.obj['hk'] = hk.HousekeeperAPI(context.obj)
    context.obj['db'] = Store(context.obj['database'])
    context.obj['lims'] = lims.LimsAPI(context.obj)


@microsalt.command()
@click.option('-d', '--dry', is_flag=True, help='print parameters to console')
@click.option('--project', 'project_id', help='link all samples for a family')
@click.argument('sample_id', required=False)
@click.pass_context
def parameter(context, dry, project_id, sample_id):
    """ Get all samples for a project """
    if project_id and (sample_id is None):
        sample_objs = context.obj['db'].microbial_order(project_id).microbial_samples
    elif sample_id and (project_id is None):
        sample_objs = [context.obj['db'].microbial_sample(sample_id)]
        project_id = sample_objs[0].microbial_order.internal_id
    elif sample_id and project_id:
        sample_objs = [
            sample_obj for sample_obj
            in context.obj['db'].microbial_order(project_id).microbial_samples
            if sample_obj.internal_id == sample_id
        ]
    else:
        LOGGER.error('provide project and/or sample')
        context.abort()

    parameters = []
    for sample_obj in sample_objs:
        method_library_prep = context.obj['lims'].get_prep_method(sample_obj.internal_id)
        method_sequencing = context.obj['lims'].get_sequencing_method(sample_obj.internal_id)
        parameter_dict = {
            'CG_ID_project': sample_obj.microbial_order.internal_id,
            'CG_ID_sample': sample_obj.internal_id,
            'Customer_ID_sample': sample_obj.name,
            'organism': sample_obj.organism.internal_id,
            'priority': sample_obj.priority,
            'reference': sample_obj.organism.reference_genome,
            'Customer_ID': sample_obj.microbial_order.customer.internal_id,
            'application_tag': sample_obj.application_version.application.tag,
            'date_arrival': sample_obj.received_at,
            'date_sequencing': sample_obj.sequenced_at,
            'date_libprep': sample_obj.prepared_at,
            'method_libprep': method_library_prep,
            'method_sequencing': method_sequencing
        }
        parameters.append(parameter_dict)

    if dry:
        outfilename = Path(context.obj['config']['usalt']['root']) / 'config' / project_id + '.json'
        print(outfilename)
        json.dumps(parameters)
    else:
        outfilename = Path(context.obj['config']['usalt']['root']) / 'config' / project_id + '.json'
        with open(outfilename, 'w') as outfile:
            json.dump(parameters, outfile)

#@microsalt.command()
#@click.option('-d', '--dry', is_flag=True, help='print command to console')
#@click.option('-p', '--parameters', required=False, help='Optional')
##@click.option('-p', '--priority', default='low', type=click.Choice(['low', 'normal', 'high']))
##@click.option('-e', '--email', help='email to send errors to')
#@click.argument('project_id')
#@click.pass_context
#def start(context, dry, parameters, project_id):
#    pass
