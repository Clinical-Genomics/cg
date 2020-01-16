"""Add CLI support to start microsalt"""

import json
import logging
from pathlib import Path
import subprocess

import click

from cg.apps import hk, lims
from cg.apps.usalt.fastq import FastqHandler
from cg.cli.workflow.microsalt.store import store as store_cmd
from cg.cli.workflow.microsalt.deliver import deliver as deliver_cmd
from cg.meta.lims.microsalt import LimsMicrosaltAPI
from cg.meta.workflow.microsalt import AnalysisAPI
from cg.meta.deliver.microsalt import DeliverAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group("microsalt")
@click.pass_context
def microsalt(context: click.Context):
    """Microbial workflow"""
    context.obj["db"] = Store(context.obj["database"])
    hk_api = hk.HousekeeperAPI(context.obj)
    lims_api = lims.LimsAPI(context.obj)
    deliver = DeliverAPI(context.obj, hk_api=hk_api, lims_api=lims_api)
    context.obj["api"] = AnalysisAPI(
        db=context.obj["db"], hk_api=hk_api, lims_api=lims_api
    )
    context.obj["lims_microsalt_api"] = LimsMicrosaltAPI(lims=lims_api)


@microsalt.command()
@click.option(
    "-o", "--order", "order_id", help="link all microbial samples for an order"
)
@click.argument("sample_id", required=False)
@click.pass_context
def link(context: click.Context, order_id: str, sample_id: str):
    """Link microbial FASTQ files for a SAMPLE_ID"""
    sample_objs = None

    if order_id and (sample_id is None):
        # link all samples in a case
        sample_objs = context.obj["db"].microbial_order(order_id).microbial_samples
    elif sample_id and (order_id is None):
        # link sample in all its families
        sample_objs = [context.obj["db"].microbial_sample(sample_id)]
    elif sample_id and order_id:
        # link only one sample in a case
        sample_objs = [context.obj["db"].microbial_sample(sample_id)]

    if not sample_objs:
        LOG.error("provide order and/or sample")
        context.abort()

    for sample_obj in sample_objs:
        LOG.info("%s: link FASTQ files", sample_obj.internal_id)
        context.obj["api"].link_sample(
            FastqHandler(context.obj),
            case=sample_obj.microbial_order.internal_id,
            sample=sample_obj.internal_id,
        )


@microsalt.command("case-config")
@click.option("-d", "--dry", is_flag=True, help="print case config to console")
@click.option("--project", "project_id", help="include all samples for a project")
@click.argument("sample_id", required=False)
@click.pass_context
def case_config(context, dry, project_id, sample_id):
    """ Create a config file on case level for microSALT """
    if project_id and (sample_id is None):
        microbial_order_obj = context.obj["db"].microbial_order(project_id)
        if not microbial_order_obj:
            LOG.error("Project %s not found", project_id)
            context.abort()
        sample_objs = microbial_order_obj.microbial_samples
    elif sample_id and (project_id is None):
        sample_obj = context.obj["db"].microbial_sample(sample_id)
        if not sample_obj:
            LOG.error("Sample %s not found", sample_id)
            context.abort()
        sample_objs = [context.obj["db"].microbial_sample(sample_id)]
    elif sample_id and project_id:
        microbial_order_obj = context.obj["db"].microbial_order(project_id)
        if not microbial_order_obj:
            LOG.error("Samples %s not found in %s ", sample_id, project_id)
            context.abort()
        sample_objs = [
            sample_obj
            for sample_obj in microbial_order_obj.microbial_samples
            if sample_obj.internal_id == sample_id
        ]
    else:
        LOG.error("provide project and/or sample")
        context.abort()

    parameters = [
        context.obj["lims_microsalt_api"].get_parameters(sample_obj)
        for sample_obj in sample_objs
    ]

    filename = project_id if project_id else sample_id
    outfilename = Path(context.obj["usalt"]["queries_path"]) / filename
    outfilename = outfilename.with_suffix(".json")
    if dry:
        print(json.dumps(parameters, indent=4, sort_keys=True))
    else:
        with open(outfilename, "w") as outfile:
            json.dump(parameters, outfile, indent=4, sort_keys=True)


@microsalt.command()
@click.option("-d", "--dry", is_flag=True, help="print command to console")
@click.option("-c", "--case-config", required=False, help="Optional")
# @click.option('-p', '--priority', default='low', type=click.Choice(['low', 'normal', 'high']))
# @click.option('-e', '--email', help='email to send errors to')
@click.argument("project_id")
@click.pass_context
def start(context, dry, case_config, project_id):
    """ Start microSALT """
    microsalt_command = context.obj["usalt"]["binary_path"]
    command = [microsalt_command]

    case_config_path = case_config
    if not case_config:
        queries_path = Path(context.obj["usalt"]["queries_path"])
        case_config_path = queries_path / project_id
        case_config_path = case_config_path.with_suffix(".json")

    command.extend(["--parameters", str(case_config_path)])
    if dry:
        print(" ".join(command))
    else:
        subprocess.run(command, shell=True, check=True)


microsalt.add_command(case_config)
microsalt.add_command(deliver_cmd)
microsalt.add_command(start)
microsalt.add_command(store_cmd)
