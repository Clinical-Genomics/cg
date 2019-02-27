"""Housekeeper API"""
import datetime as dt
import logging
import os
from pathlib import Path

from housekeeper.include import include_version, checksum as hk_checksum
from housekeeper.store import Store, models


class HousekeeperAPI(Store):
    """Housekeeper API class"""

    log = logging.getLogger(__name__)

    def __init__(self, config):
        super(HousekeeperAPI, self).__init__(config['housekeeper']['database'],
                                             config['housekeeper']['root'])
        self.root_dir = config['housekeeper']['root']

    def include(self, version_obj: models.Version):
        """Call the include version function to import related assets."""
        include_version(self.get_root_dir(), version_obj)
        version_obj.included_at = dt.datetime.now()

    def include_file(self, file_obj: models.File, version_obj: models.Version):
        """include a file and link it"""
        global_root_dir = Path(self.get_root_dir())

        # generate root directory
        version_root_dir = global_root_dir / version_obj.relative_root_dir
        version_root_dir.mkdir(parents=True, exist_ok=True)
        self.log.info('created new bundle version dir: %s', version_root_dir)

        if file_obj.to_archive:
            # calculate sha1 checksum if file is to be archived
            file_obj.checksum = HousekeeperAPI.checksum(file_obj.path)
        # hardlink file to the internal structure
        new_path = version_root_dir / Path(file_obj.path).name
        os.link(file_obj.path, new_path)
        self.log.info('linked file: %s -> %s', file_obj.path, new_path)
        file_obj.path = str(new_path).replace(f"{global_root_dir}/", '', 1)

    def re_include_file(self, new_file_path, file_obj: models.File, version_obj: models.Version):
        """re-link a file to the internal structure"""
        assert file_obj.is_included

        global_root_dir = Path(self.get_root_dir())

        # generate root directory
        version_root_dir = global_root_dir / version_obj.relative_root_dir
        version_root_dir.mkdir(parents=True, exist_ok=True)
        self.log.info('created new bundle version dir: %s', version_root_dir)

        if file_obj.to_archive:
            # calculate sha1 checksum if file is to be archived
            file_obj.checksum = HousekeeperAPI.checksum(file_obj.path)

        # hardlink file to the internal structure
        new_path = version_root_dir / Path(new_file_path).name

        # remove the old included file
        if os.path.isfile(file_obj.full_path):
            os.remove(file_obj.full_path)

        os.link(new_file_path, new_path)
        self.log.info('linked file: %s -> %s', new_file_path, new_path)
        file_obj.path = str(new_path).replace(f"{global_root_dir}/", '', 1)

    def last_version(self, bundle: str) -> models.Version:
        """gets the latest version of a bundle"""
        return (self.Version.query
                .join(models.Version.bundle)
                .filter(models.Bundle.name == bundle)
                .order_by(models.Version.created_at.desc())
                .first())

    def get_root_dir(self):
        """return the housekeeper root directory"""
        return self.root_dir

    def get_files(self, bundle: str, tags: list):
        """returns all the files in housekeeper, optionally filtered by bundle and/or tags"""
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
        return new_file

    @staticmethod
    def checksum(path):
        """Calculates and returns the checksum for a file"""
        return hk_checksum(path)
