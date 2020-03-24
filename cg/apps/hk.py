""" Module to decouple cg code from Housekeeper code """
import datetime as dt
import logging
import os
from pathlib import Path
from typing import List

from housekeeper.include import include_version, checksum as hk_checksum
from housekeeper.store import Store, models

LOG = logging.getLogger(__name__)


class HousekeeperAPI:
    """ API to decouple cg code from Housekeeper """

    def __init__(self, config):
        self._store = Store(config["housekeeper"]["database"], config["housekeeper"]["root"])
        self.root_dir = config["housekeeper"]["root"]

    def __getattr__(self, name):
        LOG.warning(
            "Called undefined method %s on %s, please implement", name, self.__class__.__name__
        )
        return getattr(self._store, name)

    def add_bundle(self, bundle_data):
        """ Build a new bundle version of files """
        return self._store.add_bundle(bundle_data)

    def new_file(
        self, path: str, checksum: str = None, to_archive: bool = False, tags: list = None
    ):
        """ Create a new file """
        return self._store.new_file(path, checksum, to_archive, tags)

    def tag(self, name: str):
        """ Fetch a tag """
        return self._store.tag(name)

    def bundle(self, name: str):
        """ Fetch a bundle """
        return self._store.bundle(name)

    def bundles(self):
        """ Fetch bundles """
        return self._store.bundles()

    def files(
        self, *, bundle: str = None, tags: List[str] = None, version: int = None, path: str = None
    ):
        """ Fetch files """
        return self._store.files(bundle=bundle, tags=tags, version=version, path=path)

    def new_tag(self, name: str, category: str = None):
        """ Create a new tag """
        return self._store.new_tag(name, category)

    def new_bundle(self, name: str, created_at: dt.datetime = None):
        """ Create a new file bundle """
        return self._store.new_bundle(name, created_at)

    def new_version(self, created_at: dt.datetime, expires_at: dt.datetime = None):
        """ Create a new bundle version """
        return self._store.new_version(created_at, expires_at)

    def add_commit(self, db_obj):
        """ Wrap method in Housekeeper Store """
        return self._store.add_commit(db_obj)

    def commit(self):
        """ Wrap method in Housekeeper Store """
        return self._store.commit()

    def session_no_autoflush(self):
        """ Wrap property in Housekeeper Store """
        return self._store.session.no_autoflush

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
            self._store.Version.query.join(models.Version.bundle)
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
        return self._store.files(bundle=bundle, tags=tags, version=version)

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
        self.add_commit(new_file)
        return new_file

    @staticmethod
    def checksum(path):
        """Calculate the checksum"""
        return hk_checksum(path)

    def initialise_db(self):
        """Create all tables in the store."""
        self._store.create_all()

    def destroy_db(self):
        """Drop all tables in the store"""
        self._store.drop_all()
