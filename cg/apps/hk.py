""" Module to decouple cg code from Housekeeper code """
import datetime as dt
import logging
import os
from pathlib import Path
from typing import List, Tuple

from housekeeper.include import checksum as hk_checksum
from housekeeper.include import include_version
from housekeeper.store import Store, models

LOG = logging.getLogger(__name__)


class HousekeeperAPI:
    """ API to decouple cg code from Housekeeper """

    def __init__(self, config: dict) -> None:
        self._store = Store(config["housekeeper"]["database"], config["housekeeper"]["root"])
        self.root_dir = config["housekeeper"]["root"]

    def __getattr__(self, name):
        LOG.warning("Called undefined %s on %s, please wrap", name, self.__class__.__name__)
        return getattr(self._store, name)

    def new_bundle(self, name: str, created_at: dt.datetime = None) -> models.Bundle:
        """ Create a new file bundle """
        return self._store.new_bundle(name, created_at)

    def add_bundle(self, bundle_data) -> Tuple[models.Bundle, models.Version]:
        """ Build a new bundle version of files """
        return self._store.add_bundle(bundle_data)

    def bundle(self, name: str) -> models.Bundle:
        """ Fetch a bundle """
        return self._store.bundle(name)

    def bundles(self) -> List[models.Bundle]:
        """ Fetch bundles """
        return self._store.bundles()

    def new_file(
        self, path: str, checksum: str = None, to_archive: bool = False, tags: list = None
    ) -> models.File:
        """ Create a new file """
        if tags is None:
            tags = []
        return self._store.new_file(path, checksum, to_archive, tags)

    def add_file(self, path, version_obj: models.Version, tags, to_archive=False) -> models.File:
        """Add a file to the database"""
        if isinstance(tags, str):
            tags = [tags]
        for tag_name in tags:
            if not self.tag(tag_name):
                self.add_tag(tag_name)

        new_file = self.new_file(
            path=str(Path(path).absolute()),
            to_archive=to_archive,
            tags=[self.tag(tag_name) for tag_name in tags],
        )

        new_file.version = version_obj
        return new_file

    def files(
        self, *, bundle: str = None, tags: List[str] = None, version: int = None, path: str = None
    ) -> List[models.File]:
        """ Fetch files """
        return self._store.files(bundle=bundle, tags=tags, version=version, path=path)

    def rollback(self):
        """ Wrap method in Housekeeper Store """
        return self._store.rollback()

    def session_no_autoflush(self):
        """ Wrap property in Housekeeper Store """
        return self._store.session.no_autoflush

    def get_files(self, bundle: str, tags: list, version: int = None):
        """Fetch all the files in housekeeper, optionally filtered by bundle and/or tags and/or
        version

        Returns:
            iterable(hk.Models.File)
        """
        return self._store.files(bundle=bundle, tags=tags, version=version)

    @staticmethod
    def get_included_path(
        root_dir: Path, version_obj: models.Version, file_obj: models.File
    ) -> Path:
        """Generate the path to a file that should be included.
        If the version dir does not exist, create a new version dir in root dir
        """
        # generate root directory
        version_root_dir = root_dir / version_obj.relative_root_dir
        version_root_dir.mkdir(parents=True, exist_ok=True)
        LOG.info("Created new bundle version dir: %s", version_root_dir)
        return version_root_dir / Path(file_obj.path).name

    def include_file(self, file_obj: models.File, version_obj: models.Version) -> models.File:
        """Call the include version function to import related assets."""
        global_root_dir = Path(self.get_root_dir())

        new_path = self.get_included_path(global_root_dir, version_obj, file_obj)
        if file_obj.to_archive:
            # calculate sha1 checksum if file is to be archived
            file_obj.checksum = HousekeeperAPI.checksum(file_obj.path)
        # hardlink file to the internal structure
        os.link(file_obj.path, new_path)
        LOG.info("Linked file: %s -> %s", file_obj.path, new_path)
        file_obj.path = str(new_path).replace(f"{global_root_dir}/", "", 1)
        return file_obj

    def new_version(
        self, created_at: dt.datetime, expires_at: dt.datetime = None
    ) -> models.Version:
        """ Create a new bundle version """
        return self._store.new_version(created_at, expires_at)

    def version(self, bundle: str, date: dt.datetime) -> models.Version:
        """ Fetch a version """
        return self._store.version(bundle, date)

    def last_version(self, bundle: str) -> models.Version:
        """Gets the latest version of a bundle"""
        return (
            self._store.Version.query.join(models.Version.bundle)
            .filter(models.Bundle.name == bundle)
            .order_by(models.Version.created_at.desc())
            .first()
        )

    def new_tag(self, name: str, category: str = None):
        """ Create a new tag """
        return self._store.new_tag(name, category)

    def add_tag(self, name: str, category: str = None):
        """ Add a tag to the database """
        tag_obj = self._store.new_tag(name, category)
        self.add_commit(tag_obj)
        return tag_obj

    def tag(self, name: str):
        """ Fetch a tag """
        return self._store.tag(name)

    def include(self, version_obj: models.Version):
        """Call the include version function to import related assets."""
        include_version(self.get_root_dir(), version_obj)
        version_obj.included_at = dt.datetime.now()

    def add_commit(self, *args, **kwargs):
        """ Wrap method in Housekeeper Store """
        return self._store.add_commit(*args, **kwargs)

    def commit(self):
        """ Wrap method in Housekeeper Store """
        return self._store.commit()

    def session_no_autoflush(self):
        """ Wrap property in Housekeeper Store """
        return self._store.session.no_autoflush

    def get_root_dir(self):
        """Returns the root dir of Housekeeper"""
        return self.root_dir

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
