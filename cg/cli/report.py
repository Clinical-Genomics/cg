# -*- coding: utf-8 -*-
import logging
import sys
import json
import click

from cg.apps.coverage import ChanjoAPI
from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.meta.analysis import AnalysisAPI
from cg.meta.deliver.api import DeliverAPI
from cg.store import Store
from cg.meta.report.api import ReportAPI

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def report(context):
    """Create Reports"""
    context.obj['db'] = Store(context.obj['database'])
    context.obj['lims'] = LimsAPI(context.obj)
    context.obj['tb'] = TrailblazerAPI(context.obj)
    context.obj['hk'] = HousekeeperAPI(context.obj)
    context.obj['deliver'] = DeliverAPI(context.obj, hk_api=context.obj['hk'], lims_api=context.obj['lims'])
    context.obj['chanjo'] = ChanjoAPI(context.obj)
    context.obj['scout'] = ScoutAPI(context.obj)
    context.obj['analysis'] = AnalysisAPI(context.obj, hk_api=context.obj['hk'],
                                          scout_api=context.obj['scout'], tb_api=context.obj['tb'],
                                          lims_api=context.obj['lims'])


@report.command()
@click.argument('customer_id')
@click.argument('family_id')
@click.pass_context
def delivery(context, customer_id, family_id):
    """Generate a delivery report for a case."""

    db = context.obj['db']
    lims = context.obj['lims']
    tb = context.obj['tb']
    deliver = context.obj['deliver']
    chanjo = context.obj['chanjo']
    analysis = context.obj['analysis']
    scout = context.obj['scout']

    report_api = ReportAPI(
        db=db,
        lims_api=lims,
        tb_api=tb,
        deliver_api=deliver,
        chanjo_api=chanjo,
        analysis_api=analysis,
        scout_api=scout,
    )

    template_out = report_api.create_delivery_report(customer_id, family_id)
    click.echo(template_out)


