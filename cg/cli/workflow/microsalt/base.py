"""Add CLI support to start microsalt"""

import json
import logging
from pathlib import Path
import subprocess

import click

from cg.apps import hk, lims
from cg.apps.usalt.fastq import FastqHandler
from cg.cli.workflow.microsalt.store import store as store_cmd
from cg.cli.workflow.microsalt.deliver import (
    deliver as deliver_cmd,
    PROJECT_TAGS,
    SAMPLE_TAGS,
)
from cg.meta.microsalt.lims import LimsMicrosaltAPI
from cg.meta.workflow.microsalt import AnalysisAPI
from cg.meta.deliver import DeliverAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group("microsalt", invoke_without_command=True)
@click.option("-o", "--order", "order_id", help="include all microbial samples for an order")
@click.pass_context
def microsalt(context: click.Context, order_id):
    """Microbial workflow"""
    context.obj["db"] = Store(context.obj["database"])
    hk_api = hk.HousekeeperAPI(context.obj)
    lims_api = lims.LimsAPI(context.obj)
    deliver = DeliverAPI(
        context.obj,
        hk_api=hk_api,
        lims_api=lims_api,
        case_tags=PROJECT_TAGS,
        sample_tags=SAMPLE_TAGS,
    )
    context.obj["api"] = AnalysisAPI(db=context.obj["db"], hk_api=hk_api, lims_api=lims_api)
    context.obj["lims_microsalt_api"] = LimsMicrosaltAPI(lims=lims_api)

    if context.invoked_subcommand is None:
        if order_id is None:
            LOG.error("Please provide an order")
            context.abort()
        else:
            # execute the analysis!
            context.invoke(config_case, order_id=order_id)
            context.invoke(link, order_id=order_id)
            context.invoke(run, order_id=order_id)


@microsalt.command()
@click.option("-o", "--order", "order_id", help="link all microbial samples for an order")
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


@microsalt.command("config-case")
@click.option("-d", "--dry", is_flag=True, help="print config-case to console")
@click.option(
    "-o",
    "--order",
    "order_id",
    help="create config-case all microbial samples for an order",
)
@click.argument("sample_id", required=False)
@click.pass_context
def config_case(context: click.Context, dry, order_id: str, sample_id: str):
    """ Create a config file on case level for microSALT """
    if order_id and (sample_id is None):
        microbial_order_obj = context.obj["db"].microbial_order(order_id)
        if not microbial_order_obj:
            LOG.error("Order %s not found", order_id)
            context.abort()
        sample_objs = microbial_order_obj.microbial_samples
    elif sample_id and (order_id is None):
        sample_obj = context.obj["db"].microbial_sample(sample_id)
        if not sample_obj:
            LOG.error("Sample %s not found", sample_id)
            context.abort()
        sample_objs = [context.obj["db"].microbial_sample(sample_id)]
    elif sample_id and order_id:
        microbial_order_obj = context.obj["db"].microbial_order(order_id)
        if not microbial_order_obj:
            LOG.error("Samples %s not found in %s ", sample_id, order_id)
            context.abort()
        sample_objs = [
            sample_obj
            for sample_obj in microbial_order_obj.microbial_samples
            if sample_obj.internal_id == sample_id
        ]
    else:
        LOG.error("provide order and/or sample")
        context.abort()

    parameters = [
        context.obj["lims_microsalt_api"].get_parameters(sample_obj) for sample_obj in sample_objs
    ]

    filename = order_id if order_id else sample_id
    outfilename = Path(context.obj["usalt"]["queries_path"]) / filename
    outfilename = outfilename.with_suffix(".json")
    if dry:
        print(json.dumps(parameters, indent=4, sort_keys=True))
    else:
        with open(outfilename, "w") as outfile:
            json.dump(parameters, outfile, indent=4, sort_keys=True)


@microsalt.command()
@click.option("-d", "--dry", is_flag=True, help="print command to console")
@click.option("-c", "--config-case", required=False, help="optionally change the config-case")
@click.argument("order_id")
@click.pass_context
def run(context, dry, config_case, order_id):
    """ Start microSALT with an order_id """
    microsalt_command = context.obj["usalt"]["binary_path"]
    command = [microsalt_command]

    config_case_path = config_case
    if not config_case:
        queries_path = Path(context.obj["usalt"]["queries_path"])
        config_case_path = queries_path / order_id
        config_case_path = config_case_path.with_suffix(".json")

    command.extend(["--parameters", str(config_case_path)])
    if dry:
        print(" ".join(command))
    else:
        LOG.info("Starting microSALT! '%s'", " ".join(command))
        subprocess.run(command, shell=True, check=True)


microsalt.add_command(config_case)
microsalt.add_command(deliver_cmd)
microsalt.add_command(run)
microsalt.add_command(store_cmd)
