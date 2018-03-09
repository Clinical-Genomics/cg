# -*- coding: utf-8 -*-
import datetime as dt
import logging
from pathlib import Path

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

    def get_files(self, bundle: str, tags: list):
        return self.files(bundle=bundle, tags=tags)

    def add_file(self, file, version_obj: models.Version, tag_name, to_archive=False):
        """Add a file to housekeeper."""
        new_file = self.new_file(
            path=str(Path(file).absolute()),
            to_archive=to_archive,
            tags=[self.tag(tag_name)]
        )
        new_file.version = version_obj
        self.add_commit(new_file)
