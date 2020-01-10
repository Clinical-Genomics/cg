"""The get_links command"""
import logging

import click
from cg.store import models

LOG = logging.getLogger(__name__)


def get_links(
    context: click.Context, case_id: str, sample_id: str
) -> [models.FamilySample]:
    """Get link objects for a SAMPLE_ID
       Args:
           case_id(str): petname
           sample_id(str): ACC6395A2
       Returns:
           link_objs(list): [models.FamilySample]
     """
    link_objs = None

    if case_id and (sample_id is None):
        LOG.info("link all samples in a case")
        case_obj = context.obj["db"].family(case_id)
        link_objs = case_obj.links
    elif sample_id and (case_id is None):
        LOG.info("link sample in all its families")
        sample_obj = context.obj["db"].sample(sample_id)

        if not sample_obj:
            LOG.error(
                "Could not find sample %s, use -c if you intended it as a case-id",
                sample_id,
            )
            context.abort()

        link_objs = sample_obj.links
    elif sample_id and case_id:
        LOG.info("link only one sample in a case")
        link_objs = [context.obj["db"].link(case_id, sample_id)]

    if not link_objs:
        LOG.error("provide case and/or sample")
        context.abort()

    return link_objs
