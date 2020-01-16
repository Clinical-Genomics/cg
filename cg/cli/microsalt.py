""" Add CLI support to start microSALT """
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
    lims_api = lims.LimsAPI(context.obj)
    context.obj['db'] = Store(context.obj['database'])
    context.obj['microsalt_api'] = MicrosaltAPI(lims=lims_api)


@microsalt.command('case-config')
@click.option('-d', '--dry', is_flag=True, help='print case config to console')
@click.option('--project', 'project_id', help='include all samples for a project')
@click.argument('sample_id', required=False)
@click.pass_context
def case_config(context, dry, project_id, sample_id):
    """ Create a config file on case level for microSALT """
    if project_id and (sample_id is None):
        microbial_order_obj = context.obj['db'].microbial_order(project_id)
        if not microbial_order_obj:
            LOGGER.error('Project %s not found', project_id)
            context.abort()
        sample_objs = microbial_order_obj.microbial_samples
    elif sample_id and (project_id is None):
        sample_obj = context.obj['db'].microbial_sample(sample_id)
        if not sample_obj:
            LOGGER.error('Sample %s not found', sample_id)
            context.abort()
        sample_objs = [context.obj['db'].microbial_sample(sample_id)]
    elif sample_id and project_id:
        microbial_order_obj = context.obj['db'].microbial_order(project_id)
        if not microbial_order_obj:
            LOGGER.error('Samples %s not found in %s ', sample_id, project_id)
            context.abort()
        sample_objs = [
            sample_obj for sample_obj
            in microbial_order_obj.microbial_samples
            if sample_obj.internal_id == sample_id
        ]
    else:
        LOGGER.error('provide project and/or sample')
        context.abort()

    parameters = [
        context.obj['microsalt_api'].get_parameters(sample_obj) for sample_obj in sample_objs
    ]

    filename = project_id if project_id else sample_id
    outfilename = Path(context.obj['usalt']['queries_path']) / filename
    outfilename = outfilename.with_suffix('.json')
    if dry:
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
    microsalt_command = context.obj['usalt']['binary_path']
    command = [microsalt_command]

    case_config_path = case_config
    if not case_config:
        queries_path = Path(context.obj['usalt']['queries_path'])
        case_config_path = queries_path / project_id
        case_config_path = case_config_path.with_suffix('.json')

    command.extend(['--parameters', str(case_config_path)])
    if dry:
        print(' '.join(command))
    else:
        subprocess.run(command, shell=True, check=True)
