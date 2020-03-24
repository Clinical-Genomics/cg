""" Module to decouple cg code from Housekeeper code """
import datetime as dt
import logging
import os
from pathlib import Path

from housekeeper.include import include_version, checksum as hk_checksum
from housekeeper.store import Store, models

LOG = logging.getLogger(__name__)


class HousekeeperAPI:
    """ API to decouple cg code from Housekeeper """

    def __init__(self, config):
        self.store = Store(config["housekeeper"]["database"], config["housekeeper"]["root"])
        self.root_dir = config["housekeeper"]["root"]

    def add_bundle(self, bundle_data):
        """ Wrap method in Housekeeper Store """
        return self.store.add_bundle(bundle_data)

    def include(self, version_obj: models.Version):
        """Call the include version function to import related assets."""
        include_version(self.get_root_dir(), version_obj)
        version_obj.included_at = dt.datetime.now()

    def include_file(self, file_obj: models.File, version_obj: models.Version):
        """Call the include version function to import related assets."""
        global_root_dir = Path(self.get_root_dir())

        # generate root directory
        version_root_dir = global_root_dir / version_obj.relative_root_dir
        version_root_dir.mkdir(parents=True, exist_ok=True)
        LOG.info("Created new bundle version dir: %s", version_root_dir)

        if file_obj.to_archive:
            # calculate sha1 checksum if file is to be archived
            file_obj.checksum = HousekeeperAPI.checksum(file_obj.path)
        # hardlink file to the internal structure
        new_path = version_root_dir / Path(file_obj.path).name
        os.link(file_obj.path, new_path)
        LOG.info("Linked file: %s -> %s", file_obj.path, new_path)
        file_obj.path = str(new_path).replace(f"{global_root_dir}/", "", 1)

    def last_version(self, bundle: str) -> models.Version:
        """Gets the latest version of a bundle"""
        return (
            self.store.Version.query.join(models.Version.bundle)
            .filter(models.Bundle.name == bundle)
            .order_by(models.Version.created_at.desc())
            .first()
        )

    def get_root_dir(self):
        """Returns the root dir of Housekeeper"""
        return self.root_dir

    def get_files(self, bundle: str, tags: list, version: int = None):
        """Fetch all the files in housekeeper, optionally filtered by bundle and/or tags and/or
        version

        Returns:
            iterable(hk.Models.File)
        """
        return self.store.files(bundle=bundle, tags=tags, version=version)

    def add_file(self, file, version_obj: models.Version, tags, to_archive=False):
        """Add a file to housekeeper."""
        if isinstance(tags, str):
            tags = [tags]
        new_file = self.new_file(
            path=str(Path(file).absolute()),
            to_archive=to_archive,
            tags=[self.tag(tag_name) for tag_name in tags],
        )

        new_file.version = version_obj
        self.store.add_commit(new_file)
        return new_file

    @staticmethod
    def checksum(path):
        return hk_checksum(path)
