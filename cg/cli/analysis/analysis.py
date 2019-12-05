# -*- coding: utf-8 -*-
import logging
import shutil
import sys
from pathlib import Path

import click
from cg.apps import hk, tb, scoutapi, lims
from cg.apps.balsamic.fastq import BalsamicFastqHandler
from cg.apps.mip.fastq import MipFastqHandler
from cg.exc import LimsDataError
from cg.meta.analysis import AnalysisAPI
from cg.meta.deliver.api import DeliverAPI
from cg.store import Store

LOG = logging.getLogger(__name__)
PRIORITY_OPTION = click.option('-p', '--priority', type=click.Choice(['low', 'normal', 'high']))
EMAIL_OPTION = click.option('-e', '--email', help='email to send errors to')
START_WITH_PROGRAM = click.option('-sw', '--start-with', help='start mip from this program.')


@click.group(invoke_without_command=True)
@PRIORITY_OPTION
@EMAIL_OPTION
@START_WITH_PROGRAM
@click.option('-f', '--family', 'family_id', help='family to prepare and start an analysis for')
@click.pass_context
def analysis(context, priority, email, family_id, start_with):
    """Prepare and start a MIP analysis for a FAMILY_ID."""
    context.obj['db'] = Store(context.obj['database'])
    hk_api = hk.HousekeeperAPI(context.obj)
    scout_api = scoutapi.ScoutAPI(context.obj)
    lims_api = lims.LimsAPI(context.obj)
    context.obj['tb'] = tb.TrailblazerAPI(context.obj)
    deliver = DeliverAPI(context.obj, hk_api=hk_api, lims_api=lims_api)
    context.obj['api'] = AnalysisAPI(
        db=context.obj['db'],
        hk_api=hk_api,
        tb_api=context.obj['tb'],
        scout_api=scout_api,
        lims_api=lims_api,
        deliver_api=deliver
    )

    if context.invoked_subcommand is None:
        if family_id is None:
            _suggest_cases_to_analyze(context, show_as_error=True)
            context.abort()

        # check everything is ok
        family_obj = context.obj['db'].family(family_id)
        if family_obj is None:
            LOG.error(f"{family_id} not found")
            context.abort()
        is_ok = context.obj['api'].check(family_obj)
        if not is_ok:
            LOG.warning(f"{family_obj.internal_id}: not ready to start")
            # commit the updates to request flowcells
            context.obj['db'].commit()
        else:
            # execute the analysis!
            context.invoke(case_config, family_id=family_id)
            context.invoke(link, family_id=family_id)
            context.invoke(panel, family_id=family_id)
            context.invoke(start, family_id=family_id, priority=priority, email=email,
                           start_with=start_with)


def _suggest_cases_to_analyze(context, show_as_error=False):
    if show_as_error:
        LOG.error('provide a case, suggestions:')
    else:
        LOG.warning('provide a case, suggestions:')
    for family_obj in context.obj['db'].cases_to_mip_analyze()[:50]:
        click.echo(family_obj)


@analysis.command()
@click.option('-f', '--family', 'family_id', help='link all samples for a family')
@click.argument('sample_id', required=False)
@click.pass_context
def link(context, family_id, sample_id):
    """Link FASTQ files for a SAMPLE_ID."""

    link_objs = None

    if family_id and (sample_id is None):
        # link all samples in a family
        family_obj = context.obj['db'].family(family_id)
        link_objs = family_obj.links
    elif sample_id and (family_id is None):
        # link sample in all its families
        sample_obj = context.obj['db'].sample(sample_id)
        link_objs = sample_obj.links
    elif sample_id and family_id:
        # link only one sample in a family
        link_objs = [context.obj['db'].link(family_id, sample_id)]

    if not link_objs:
        LOG.error('provide family and/or sample')
        context.abort()

    for link_obj in link_objs:
        LOG.info("%s: %s link FASTQ files", link_obj.sample.internal_id,
                 link_obj.sample.data_analysis)
        if link_obj.sample.data_analysis and 'balsamic' in link_obj.sample.data_analysis.lower():
            context.obj['api'].link_sample(BalsamicFastqHandler(context.obj),
                                           case=link_obj.family.internal_id,
                                           sample=link_obj.sample.internal_id)
        elif not link_obj.sample.data_analysis or \
                'mip' in link_obj.sample.data_analysis.lower() or \
                'mip-rna' in link_obj.sample.data_analysis.lower():
            mip_fastq_handler = MipFastqHandler(context.obj,
                                                context.obj['db'],
                                                context.obj['tb'])
            context.obj['api'].link_sample(mip_fastq_handler,
                                           case=link_obj.family.internal_id,
                                           sample=link_obj.sample.internal_id)
