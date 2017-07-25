# -*- coding: utf-8 -*-
import logging
from typing import Callable

import petname

log = logging.getLogger(__name__)


def get_unique_id(availability_func: Callable) -> str:
    """Generate a unique sample id.

    The availability function should return a matching result given an id if it
    already exists.
    """
    while True:
        random_id = petname.Generate(3, separator='')
        if availability_func(random_id) is None:
            return random_id
        else:
            log.debug(f"{random_id} already used - trying another id")
