# -*- coding: utf-8 -*-
from housekeeper.store import api


def connect(config):
    """Connect to the Housekeeper database."""
    hk_db = api.manager(config['housekeeper']['database'])
    return hk_db
