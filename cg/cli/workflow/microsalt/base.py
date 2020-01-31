"""Add CLI support to start microsalt"""

import logging

import click

from cg.apps import hk, lims
from cg.apps.usalt.fastq import FastqHandler
from cg.cli.workflow.microsalt.store import store as store_cmd
from cg.cli.workflow.microsalt.deliver import (
    deliver as deliver_cmd,
    PROJECT_TAGS,
    SAMPLE_TAGS,
)
from cg.meta.workflow.microsalt import AnalysisAPI
from cg.meta.deliver import DeliverAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group("microsalt")
@click.pass_context
def microsalt(context: click.Context):
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
    context.obj["api"] = AnalysisAPI(
        db=context.obj["db"], hk_api=hk_api, lims_api=lims_api
    )


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


microsalt.add_command(store_cmd)
microsalt.add_command(deliver_cmd)
