"""The get_links command"""
import logging
from typing import List

import click

from cg.store import Store, models

LOG = logging.getLogger(__name__)


def get_links(
    store: Store, case_id: str = None, sample_id: str = None, ticket: int = None
) -> List[models.FamilySample]:
    """Get link objects for a SAMPLE_ID
    Args:
        case_id(str): petname
        sample_id(str): ACC6395A2
        ticket(int): 123456
    Returns:
        link_objs(list): [models.FamilySample]
    """

    if not any([case_id, sample_id, ticket]):
        LOG.error("Please provide case, sample and/or ticket")
        raise click.Abort

    link_objs = store.links(case_id, sample_id, ticket).all()

    if not link_objs:
        LOG.error("Could not find any links")
        raise click.Abort

    return link_objs
