""" Add CLI support to start microSALT """
from datetime import datetime
import json
import logging
import subprocess
from pathlib import Path

import click

from cg.apps import lims
from cg.meta.lims.microsalt import MicrosaltAPI
from cg.store import Store

LOGGER = logging.getLogger(__name__)


@click.group()
@click.pass_context
def microsalt(context):
    """ Run microbial workflow """
    context.obj['db'] = Store(context.obj['database'])
    context.obj['lims_api'] = lims.LimsAPI(context.obj)
    context.obj['microsalt_api'] = MicrosaltAPI(lims=context.obj['lims_api'])


@microsalt.command('case-config')
@click.option('-d', '--dry', is_flag=True, help='print case config to console')
@click.option('--project', 'project_id', help='include all samples for a project')
@click.argument('sample_id', required=False)
@click.pass_context
def case_config(context, dry, project_id, sample_id):
    """ Create a config file on case level for microSALT """
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

    parameters = []
    for sample_obj in sample_objs:
        method_library_prep = context.obj['lims_api'].get_prep_method(sample_obj.internal_id)
        method_sequencing = context.obj['lims_api'].get_sequencing_method(sample_obj.internal_id)
        organism = context.obj['microsalt_api'].get_organism(sample_obj)
        priority = 'research' if sample_obj.priority == 0 else 'standard'

        parameter_dict = {
            'CG_ID_project': sample_obj.microbial_order.internal_id,
            'CG_ID_sample': sample_obj.internal_id,
            'Customer_ID_sample': sample_obj.name,
            'organism': organism,
            'priority': priority,
            'reference': sample_obj.organism.reference_genome,
            'Customer_ID': sample_obj.microbial_order.customer.internal_id,
            'application_tag': sample_obj.application_version.application.tag,
            'date_arrival': str(sample_obj.received_at or datetime.min),
            'date_sequencing': str(sample_obj.sequenced_at or datetime.min),
            'date_libprep': str(sample_obj.prepared_at or datetime.min),
            'method_libprep': method_library_prep or 'Not in LIMS',
            'method_sequencing': method_sequencing or 'Not in LIMS',
        }
        parameters.append(parameter_dict)

    filename = project_id if project_id else sample_id
    outfilename = Path(context.obj['microsalt']['queries_path']) / filename
    outfilename = outfilename.with_suffix('.json')
    if dry:
        print(outfilename)
        print(json.dumps(parameters, indent=4, sort_keys=True))
    else:
        with open(outfilename, 'w') as outfile:
            json.dump(parameters, outfile, indent=4, sort_keys=True)


@microsalt.command()
@click.option('-d', '--dry', is_flag=True, help='print command to console')
@click.option('-c', '--case-config', required=False, help='Optional')
# @click.option('-p', '--priority', default='low', type=click.Choice(['low', 'normal', 'high']))
# @click.option('-e', '--email', help='email to send errors to')
@click.argument('project_id')
@click.pass_context
def start(context, dry, case_config, project_id):
    """ Start microSALT """
    microsalt_command = context.obj['microsalt']['binary_path']
    command = [microsalt_command]

    case_config_path = case_config
    if not case_config:
        queries_path = Path(context.obj['microsalt']['queries_path'])
        case_config_path = queries_path / project_id
        case_config_path = case_config_path.with_suffix('.json')

    command.extend(['--parameters', str(case_config_path)])
    if dry:
        print(' '.join(command))
    else:
        process = subprocess.run(command, shell=True)
        return process
