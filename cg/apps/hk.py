# -*- coding: utf-8 -*-
from housekeeper.store import Store


class HousekeeperAPI(Store):
    """docstring for HousekeeperAPI"""

    def __init__(self, config):
        super(HousekeeperAPI, self).__init__(config['housekeeper']['database'])
