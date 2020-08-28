"""The get_links command"""
import logging
from typing import List

import click

from cg.store import Store, models

LOG = logging.getLogger(__name__)


def get_links(
    store: Store, case_id: str = None, sample_id: str = None
) -> List[models.FamilySample]:
    """Get link objects for a SAMPLE_ID
    Args:
        case_id(str): petname
        sample_id(str): ACC6395A2
    Returns:
        link_objs(list): [models.FamilySample]
    """
    link_objs = []

    if case_id and sample_id:
        LOG.info("Link only one sample in a case")
        link_obj = store.link(family_id=case_id, sample_id=sample_id)
        if not link_obj:
            LOG.error("Could not find link for case %s and sample %s", case_id, sample_id)
            raise click.Abort
        link_objs = [link_obj]

    elif case_id:
        LOG.info("Link all samples in a case")
        case_obj = store.family(case_id)
        if not case_obj:
            LOG.error("Could not find case %s", case_id)
            raise click.Abort

        if not case_obj.links:
            LOG.error("Could not find links for case %s", case_id)
            raise click.Abort

        link_objs = case_obj.links

    elif sample_id:
        LOG.info("Link sample %s in all its families", sample_id)
        sample_obj = store.sample(sample_id)

        if not sample_obj:
            LOG.error(
                "Could not find sample %s. Did you intend %s as a case-id?",
                sample_id,
                sample_id,
            )
            raise click.Abort

        if not sample_obj.links:
            LOG.error("Could not find links for sample %s", sample_id)
            raise click.Abort

        link_objs = sample_obj.links

    else:
        LOG.error("Please provide case and/or sample")
        raise click.Abort

    return link_objs
