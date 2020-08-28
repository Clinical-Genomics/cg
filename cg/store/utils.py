import logging
from typing import Callable

import petname
from cg.store import models

LOG = logging.getLogger(__name__)


def case_exists(case_obj, case_id: str):
    """
    Check that case exist in Store
    """
    if case_obj is None:
        LOG.error("%s: case not found", case_id)
        return None
    return True


def get_links(case: models.Family) -> models.Sample:
    """Return all samples from a family object"""
    for sample_obj in case.links:
        yield sample_obj


def get_samples(analysis_obj: models.Analysis) -> models.Sample:
    """Search a analysis object and return the samples"""
    return get_links(analysis_obj.family)


def get_unique_id(availability_func: Callable) -> str:
    """Generate a unique sample id.

    The availability function should return a matching result given an id if it
    already exists.
    """
    while True:
        random_id = petname.Generate(3, separator="")
        if availability_func(random_id) is None:
            return random_id
        else:
            LOG.debug(f"{random_id} already used - trying another id")


def reset_case_action(case_obj):
    """ Resets action on case """

    case_obj.action = None
