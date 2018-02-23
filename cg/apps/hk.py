# -*- coding: utf-8 -*-
import datetime as dt
import logging

from housekeeper.exc import VersionIncludedError
from housekeeper.include import include_version
from housekeeper.store import Store, models

log = logging.getLogger(__name__)


class HousekeeperAPI(Store):

    def __init__(self, config):
        super(HousekeeperAPI, self).__init__(config['housekeeper']['database'],
                                             config['housekeeper']['root'])
        self.root_dir = config['housekeeper']['root']

    def include(self, version_obj: models.Version):
        """Call the include version function to import related assets."""
        include_version(self.root_dir, version_obj)
        version_obj.included_at = dt.datetime.now()

    def last_version(self, bundle: str) -> models.Version:
        return (self.Version.query
                            .join(models.Version.bundle)
                            .filter(models.Bundle.name == bundle)
                            .order_by(models.Version.created_at.desc())
                            .first())

    def get_root_dir(self):
        return self.root_dir
