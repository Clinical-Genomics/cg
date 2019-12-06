"""Common CLI analysis functions"""

import click
import logging

LOG = logging.getLogger(__name__)

@click.group()
def analysis():
    """Analysis work flows commands"""
    pass


def get_link_objs(context, case_id, sample_id):
    """Get link objects for a SAMPLE_ID."""

    link_objs = None

    if case_id and (sample_id is None):
        # link all samples in a case
        case_obj = context.obj['db'].family(case_id)
        link_objs = case_obj.links
    elif sample_id and (case_id is None):
        # link sample in all its families
        sample_obj = context.obj['db'].sample(sample_id)
        link_objs = sample_obj.links
    elif sample_id and case_id:
        # link only one sample in a case
        link_objs = [context.obj['db'].link(case_id, sample_id)]

    if not link_objs:
        LOG.error('provide case and/or sample')
        context.abort()

    return link_objs
