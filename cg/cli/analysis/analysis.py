"""Common CLI analysis functions"""

import click
import logging

LOG = logging.getLogger(__name__)

@click.group()
def analysis():
    """Analysis work flows commands"""
    pass


def get_link_objs(context, family_id, sample_id):
    """Get link objects for a SAMPLE_ID."""

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

    return link_objs
